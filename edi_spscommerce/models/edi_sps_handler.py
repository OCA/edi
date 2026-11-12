# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging
import os

from odoo import api, models
from odoo.exceptions import UserError

from odoo.addons.edi_core_oca.exceptions import EDIValidationError

from ..services import rsx

_logger = logging.getLogger(__name__)


class EdiSpsHandler(models.AbstractModel):
    """SPS Commerce RSX handlers.

    One model implements every handler role so that a single ir.model
    record can be referenced by all ``*_model_id`` fields of the exchange
    types (sps_orders_in / sps_shipments_out / sps_invoices_out).

    Transport has two modes, selected automatically per exchange record:

    - **Storage (SPS SFTP)**: when the backend's ``storage_id`` is set,
      ``receive``/``send``/``check`` delegate to
      ``edi.oca.storage.handler`` which reads/writes files under the
      backend's ``*_dir_*`` directories (SPS layout: ``out``/``testout``
      inbound, ``in``/``testin`` outbound, ``archive`` for processed).
    - **Manual drop (fallback)**: with no storage configured, ``receive``
      returns content attached to the exchange record (import wizard /
      form) and ``send`` writes the payload to ``rsx.outbound_dir``::

        rsx:
          outbound_dir: /tmp/edi-sps-out
    """

    _name = "edi.sps.handler"
    _inherit = [
        "edi.oca.storage.handler",
        "edi.oca.handler.process",
        "edi.oca.handler.input.validate",
        "edi.oca.handler.output.validate",
        "edi.oca.handler.generate",
    ]
    _description = "SPS Commerce RSX EDI handler"

    # ------------------------------------------------------------------
    # Inbound
    # ------------------------------------------------------------------
    def receive(self, exchange_record):
        """Fetch the payload: attached content first, storage second.

        Attached content wins so the import wizard and manual exchange
        records keep working even when the backend has a storage
        configured. Records created by the storage poller carry only a
        filename, so they fall through to the remote fetch.
        """
        content = exchange_record._get_file_content()
        if content:
            return content
        return super().receive(exchange_record)

    def input_validate(self, exchange_record, value=None, **kw):
        """Validate the received payload is RSX XML of the expected document."""
        payload = value if value is not None else exchange_record._get_file_content()
        return self._validate_payload(exchange_record, payload)

    def _validate_payload(self, exchange_record, payload):
        """Reject payloads that are not RSX XML of the expected document.

        Shared by input_validate (received files) and output_validate
        (generated files). The exchange type's ``rsx.document`` setting
        decides the expected root element.
        """
        try:
            data = rsx.parse(payload)
        except ValueError as err:
            raise EDIValidationError(str(err)) from err
        expected = self._expected_document(exchange_record)
        if expected and rsx.root_document(data) != expected:
            raise EDIValidationError(
                f"Expected RSX {expected} document, got <{rsx.root_name(data)}>."
            )
        rsx_conf = self._rsx_settings(exchange_record)
        if rsx_conf.get("xsd_validate"):
            schema_path = rsx_conf.get("xsd_path")
            if not schema_path:
                raise EDIValidationError(
                    "rsx.xsd_validate is enabled but rsx.xsd_path is not set."
                )
            errors = rsx.xsd_validate(payload, schema_path)
            if errors:
                raise EDIValidationError(
                    "RSX payload failed XSD validation:\n" + "\n".join(errors[:10])
                )
        return True

    def process(self, exchange_record):
        """Parse the received payload and create business documents."""
        payload = exchange_record._get_file_content()
        document = self._expected_document(exchange_record)
        if document == "orders":
            return self._process_orders(exchange_record, payload)
        if document == "order_acks":
            return self._process_order_acks(exchange_record, payload)
        raise UserError(self.env._("No RSX processor implemented for '%s'.", document))

    def _process_order_acks(self, exchange_record, payload):
        """Apply RSX <OrderAck> headers to matching sale orders.

        Acks that match no order are logged and skipped — one bad ack
        must not fail the whole batch.
        """
        acks = rsx.parse_order_acks(payload)
        if not acks:
            raise UserError(
                self.env._("OrderAcks payload contains no <OrderAck> documents.")
            )
        SaleOrder = self.env["sale.order"]
        matched = self.env["sale.order"]
        for ack in acks:
            order = SaleOrder._edi_sps_apply_ack(ack)
            if order:
                matched |= order
            else:
                po = (
                    (ack.get("Header") or {})
                    .get("OrderHeader", {})
                    .get("PurchaseOrderNumber")
                )
                _logger.warning(
                    "SPS OrderAck for PO %s matched no sale order; skipped.",
                    po,
                )
        return matched

    def _process_orders(self, exchange_record, payload):
        """Create one draft sale.order per <Order> in the payload.

        Batched files are split: this record imports the first <Order>
        and spawns one sibling exchange record per remaining <Order>,
        each carrying a single-order payload in ``input_received`` state
        so it flows through the normal process pipeline (and can be
        retried/inspected individually).
        """
        orders = rsx.parse_orders(payload)
        if not orders:
            raise UserError(self.env._("Orders payload contains no <Order> documents."))
        sale_order = self.env["sale.order"]._edi_sps_import_order(orders[0])
        exchange_record._set_related_record(sale_order)
        sale_order._edi_set_origin(exchange_record)
        for order in orders[1:]:
            self._split_order_record(exchange_record, order)
        return sale_order

    def _split_order_record(self, exchange_record, order):
        """Create a child exchange record holding one <Order> payload."""
        header = (order.get("Header") or {}).get("OrderHeader") or {}
        po_ref = header.get("PurchaseOrderNumber") or "order"
        filename = exchange_record.exchange_filename or exchange_record.identifier
        child = exchange_record.backend_id.create_record(
            exchange_record.type_id.code,
            {
                "parent_id": exchange_record.id,
                "exchange_filename": f"{filename}#{po_ref}",
                "edi_exchange_state": "input_received",
            },
        )
        child._set_file_content(rsx.serialize_orders(order))
        return child

    # ------------------------------------------------------------------
    # Outbound
    # ------------------------------------------------------------------
    def generate(self, exchange_record):
        """Render the outbound payload via the type's QWeb output template.

        Document structure *and* the RSX -> Odoo field mapping live in the
        ``edi.exchange.template.output`` QWeb document: the template
        consumes the business record directly (``record`` /
        ``exchange_record`` / ``backend`` are already in the render
        context). This method only injects ``meta`` (envelope ids from the
        exchange-type settings) — the template's customization surface
        needs no code.
        """
        record = exchange_record.record
        if not record:
            raise UserError(
                self.env._(
                    "Exchange record %s has no related business record.",
                    exchange_record.identifier,
                )
            )
        tmpl = exchange_record.backend_id._get_output_template(exchange_record)
        if not tmpl:
            raise UserError(
                self.env._(
                    "No output template found for exchange type %s. "
                    "Set an edi.exchange.template.output on the type.",
                    exchange_record.type_id.name,
                )
            )
        return tmpl.exchange_generate(
            exchange_record,
            meta=self._prepare_meta_values(exchange_record, record),
        )

    def _prepare_meta_values(self, exchange_record, record):
        """Resolve RSX Meta sender/receiver ids for outbound documents.

        Precedence: ``rsx.sender_id`` / ``rsx.receiver_id`` exchange-type
        settings, then partner ref/name for the receiver.
        """
        rsx_conf = self._rsx_settings(exchange_record)
        sender = rsx_conf.get("sender_id") or "PROSLAT"
        receiver = (
            rsx_conf.get("receiver_id")
            or getattr(record.partner_id, "x_sps_trading_partner_id", False)
            or record.partner_id.ref
            or record.partner_id.name
            or "CUSTOMER"
        )
        return {
            "sender_unique_id": sender,
            "receiver_unique_id": receiver,
            "interchange_sender_id": sender,
            "interchange_receiver_id": receiver,
        }

    def output_validate(self, exchange_record, value=None, **kw):
        payload = value if value is not None else exchange_record._get_file_content()
        return self._validate_payload(exchange_record, payload)

    def send(self, exchange_record):
        """Deliver the payload: storage transport first, local dir fallback.

        With a storage set, delegates to
        ``edi.oca.storage.handler.send`` which uploads to
        ``output_dir_pending`` on the remote filesystem. Otherwise writes
        the payload to ``rsx.outbound_dir`` (manual fallback).
        """
        if exchange_record.backend_id.storage_id:
            return super().send(exchange_record)
        rsx_conf = self._rsx_settings(exchange_record)
        out_dir = rsx_conf.get("outbound_dir") or "./edi-sps-out"
        content = exchange_record._get_file_content(binary=False)
        raw = base64.b64decode(content) if content else b""
        if not raw:
            raise UserError(
                self.env._(
                    "Exchange record %s has no payload to send.",
                    exchange_record.identifier,
                )
            )
        os.makedirs(out_dir, exist_ok=True)
        filename = exchange_record.exchange_filename or exchange_record.identifier
        path = os.path.join(out_dir, filename)
        with open(path, "wb") as f:
            f.write(raw)
        _logger.info("SPS RSX: wrote %s to %s", filename, path)
        return True

    def check(self, exchange_record):
        """Poll remote done/error dirs — only meaningful with a storage."""
        if not exchange_record.backend_id.storage_id:
            return False
        return super().check(exchange_record)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _rsx_settings(self, exchange_record):
        settings = exchange_record.type_id.get_settings() or {}
        return settings.get("rsx") or {}

    @api.model
    def _expected_document(self, exchange_record):
        """Return the RSX document key for the exchange type.

        Reads ``rsx.document`` from the exchange type advanced settings;
        falls back to the type code (``sps_orders_in`` -> ``orders``).
        """
        document = self._rsx_settings(exchange_record).get("document")
        if document:
            return document
        code = exchange_record.type_id.code or ""
        for key in rsx.DOC_ROOTS:
            if key in code:
                return key
        return None
