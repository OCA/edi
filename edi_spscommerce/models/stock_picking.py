# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "edi.exchange.consumer.mixin"]

    def button_validate(self):
        res = super().button_validate()
        # Queue an outbound Shipments exchange for validated pickings.
        self._edi_sps_queue_shipments()
        return res

    def _edi_sps_queue_shipments(self, force=False):
        """Queue an RSX Shipments (ASN) exchange per done picking.

        Split out of ``button_validate`` so it can be retriggered manually
        (server action, mass retry after a transient failure). Skips
        pickings that already have an exchange record unless ``force``.
        Returns the related exchange records.
        """
        exchange_type = self.env["edi.exchange.type"].search(
            [("code", "=", "sps_shipments_out"), ("direction", "=", "output")],
            limit=1,
        )
        if not exchange_type:
            return self.env["edi.exchange.record"]
        records = self.env["edi.exchange.record"]
        for picking in self.filtered(lambda p: p.state == "done"):
            if not exchange_type.is_partner_enabled(picking.partner_id):
                continue
            if not force and picking._has_exchange_record(exchange_type):
                continue
            try:
                picking._edi_send_via_edi(exchange_type)
                records |= picking._get_exchange_record(exchange_type)
            except Exception as err:  # noqa: BLE001 - never block validation
                _logger.warning(
                    "SPS Shipments queue failed for picking %s: %s",
                    picking.name,
                    err,
                )
        return records
