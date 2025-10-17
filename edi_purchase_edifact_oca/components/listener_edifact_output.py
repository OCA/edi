# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PurchaseOrderEdifactListener(Component):
    _name = "purchase.order.event.listener.edifact"
    _inherit = "base.event.listener"
    _apply_on = ["purchase.order"]

    def on_button_confirm_purchase_order(self, order):
        if not self._should_create_exchange_record(order):
            return None

        domain = [
            "|",
            "|",
            ("partner_ids", "=", False),
            ("partner_ids", "=", order.partner_id.id),
            ("partner_ids", "=", order.partner_id.commercial_partner_id.id),
        ]
        exchange_type = self.env["edi.exchange.type"].sudo().search(domain, limit=1)
        if not exchange_type:
            return None

        record = exchange_type.backend_id.create_record(
            exchange_type.code, self._storage_new_exchange_record_vals()
        )
        # Set related record
        record._set_related_record(order)
        _logger.info(
            "Exchange record for purchase order %s was created: %s",
            order.name,
            record.identifier,
        )

    def _should_create_exchange_record(self, order):
        if self.env.context.get("skip_send_edifact", False):
            return False

        partner = order.partner_id
        if not partner:
            return False

        return (
            partner.edifact_purchase_order_out
            or partner.parent_id.edifact_purchase_order_out
        )

    def _storage_new_exchange_record_vals(self):
        return {"edi_exchange_state": "new"}
