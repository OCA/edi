# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging
import os

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.edi_core_oca.exceptions import EDIValidationError
from odoo.addons.edi_spscommerce.services import rsx

_logger = logging.getLogger(__name__)


class EdiSpsHandler(models.AbstractModel):
    """SPS Commerce RSX handlers.

    One model implements every handler role so that a single ir.model
    record can be referenced by all ``*_model_id`` fields of the exchange
    types (sps_orders_in / sps_shipments_out / sps_invoices_out).

    Transport has two modes, selected automatically per exchange record:

    - **Storage (SPS SFTP)**: when ``exchange_record.backend_id.storage_id``
      is set, ``receive``/``send``/``check`` delegate to
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
                f"Expected RSX {expected} document, got "
                f"<{rsx.root_name(data)}>."
            )
        # TODO: optional XSD validation behind rsx.xsd_validate
        # (lxml.etree.XMLSchema against user-supplied 7.7.0 schemas —
        # the schemas are SPS material and are not shipped).
        return True

    def process(self, exchange_record):
        """Parse the received payload and create business documents."""
        payload = exchange_record._get_file_content()
        document = self._expected_document(exchange_record)
        if document == "orders":
            return self._process_orders(exchange_record, payload)
        raise UserError(f"No RSX processor implemented for '{document}'.")

    def _process_orders(self, exchange_record, payload):
        """Create one draft sale.order per <Order> in the payload.

        TODO(design): split batched files into one exchange record per
        <Order> at receive — currently a single record processes them all
        and is related to the first created order.
        """
        orders = rsx.parse_orders(payload)
        if not orders:
            raise UserError("Orders payload contains no <Order> documents.")
        sale_orders = self.env["sale.order"]
        for order in orders:
            sale_orders |= self._create_sale_order(order)
        exchange_record._set_related_record(sale_orders[:1])
        sale_orders[:1]._edi_set_origin(exchange_record)
        return sale_orders

    def _create_sale_order(self, order):
        # RSX element names are kept verbatim by the codec, so the reads
        # below match the SPS documentation (Header/OrderHeader/...).
        order_header = (order.get("Header") or {}).get("OrderHeader") or {}
        po_number = order_header.get("PurchaseOrderNumber")
        if not po_number:
            raise UserError("Order has no PurchaseOrderNumber.")
        purpose = order_header.get("TsetPurposeCode") or "00"
        if purpose != "00":
            raise UserError(
                f"Unsupported TsetPurposeCode '{purpose}': only '00' "
                "(original) is implemented. Cancel/change orders need "
                "manual handling."
            )
        meta = order.get("Meta") or {}
        partner = self._find_partner(
            order_header.get("TradingPartnerId"),
            meta.get("InterchangeSenderID"),
            meta.get("SenderUniqueID"),
        )
        if not partner:
            raise UserError(
                "No partner found for trading partner "
                f"'{order_header.get('TradingPartnerId')}'. Set the "
                "customer's Internal Reference to the SPS trading "
                "partner id."
            )
        existing = self.env["sale.order"].search(
            [
                ("partner_id", "=", partner.id),
                ("client_order_ref", "=", po_number),
            ],
            limit=1,
        )
        if existing:
            raise UserError(
                f"Sale order {existing.name} already exists for PO "
                f"{po_number} / {partner.name}."
            )
        order_vals = self._prepare_sale_order_values(order, partner)
        return self.env["sale.order"].create(order_vals)

    def _prepare_sale_order_values(self, order, partner):
        header = order.get("Header") or {}
        order_header = header.get("OrderHeader") or {}
        commitment_date = next(
            (
                d["Date"]
                for d in header.get("Dates") or []
                if d.get("DateTimeQualifier") == "002" and d.get("Date")
            ),
            None,
        )
        order_lines = []
        for line_item in order.get("LineItem") or []:
            line = line_item.get("OrderLine") or {}
            product = self._find_product(line, partner)
            if not product:
                raise UserError(
                    "No product found for item ids "
                    f"{line} on line "
                    f"{line.get('LineSequenceNumber')}."
                )
            order_lines.append(
                Command.create(
                    {
                        "product_id": product.id,
                        "product_uom_qty": self._to_float(line.get("OrderQty")),
                        "price_unit": self._to_float(line.get("PurchasePrice")),
                    }
                )
            )
        if not order_lines:
            raise UserError(
                "Order "
                f"{order_header.get('PurchaseOrderNumber')} has no order "
                "lines."
            )
        return {
            "partner_id": partner.id,
            "client_order_ref": order_header.get("PurchaseOrderNumber"),
            "date_order": order_header.get("PurchaseOrderDate") or fields.Datetime.now(),
            "commitment_date": commitment_date,
            "order_line": order_lines,
            # TODO: partner_shipping_id from Address[ST] (x_sps_location
            # match, then auto-create child delivery address), payment
            # terms, currency, notes, dropship customer refs — see
            # docs/EDI_SPSCOMMERCE.md mapping tables.
        }

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
                f"Exchange record {exchange_record.identifier} has no "
                "related business record."
            )
        tmpl = exchange_record.backend_id._get_output_template(exchange_record)
        if not tmpl:
            raise UserError(
                f"No output template found for exchange type "
                f"{exchange_record.type_id.name}. Set an "
                "edi.exchange.template.output on the type."
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

        With ``backend_id.storage_id`` set, delegates to
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
                f"Exchange record {exchange_record.identifier} has no "
                "payload to send."
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

    @api.model
    def _find_partner(self, *refs):
        """Find res.partner by Internal Reference, trying each ref in order."""
        for ref in refs:
            if ref:
                partner = self.env["res.partner"].search(
                    [("ref", "=", str(ref).strip())], limit=1
                )
                if partner:
                    return partner
        return self.env["res.partner"]

    @api.model
    def _find_product(self, order_line, partner):
        """Find product.product via the RSX part-number match chain.

        ``order_line`` is the raw <OrderLine> dict — it doubles as the
        item-id block. Priority (design doc): VendorPartNumber/
        ApplicationId -> default_code; BuyerPartNumber ->
        product.customer.code; GTIN/EAN/ConsumerPackageCode -> barcode.
        """
        Product = self.env["product.product"]
        for key in ("VendorPartNumber", "ApplicationId"):
            code = (order_line.get(key) or "").strip()
            if code:
                product = Product.search([("default_code", "=", code)], limit=1)
                if product:
                    return product
        buyer_code = (order_line.get("BuyerPartNumber") or "").strip()
        if buyer_code and self.env.registry.get("product.customer.code"):
            customer_code = self.env["product.customer.code"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("product_code", "=", buyer_code),
                ],
                limit=1,
            )
            if customer_code and "product_id" in customer_code._fields:
                return customer_code.product_id
        for key in ("GTIN", "EAN", "ConsumerPackageCode"):
            code = (order_line.get(key) or "").strip()
            if code:
                product = Product.search([("barcode", "=", code)], limit=1)
                if product:
                    return product
        return Product

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
