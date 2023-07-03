# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahaw@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__file__)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = [
        "sale.order",
        "edi.state.consumer.mixin",
    ]

    # See data/edi_state.xml
    # order
    EDI_STATE_ORDER_ACCEPTED = "AP"
    EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED = "CA"
    EDI_STATE_ORDER_MSG_ACK = "AB"
    EDI_STATE_ORDER_REJECTED = "RE"
    EDI_STATE_ORDER_LINE_ADDED = "1"
    EDI_STATE_ORDER_LINE_CHANGED = "3"
    EDI_STATE_ORDER_LINE_ACCEPTED = "5"
    EDI_STATE_ORDER_LINE_NOT_ACCEPTED = "7"
    EDI_STATE_ORDER_LINE_ALREADY_DELIVERED = "42"

    def _edi_update_state(self, lines=None):
        metadata = self._edi_get_metadata()
        orig_vals = metadata.get("orig_values", {})
        line_vals = orig_vals.get("lines", {})
        if not orig_vals.get("lines"):
            _logger.debug(
                "_edi_update_state: no line value found for order %s", self.id
            )
        # TODO: test
        lines = lines or self.order_line
        lines._edi_determine_lines_state(line_vals)
        state_code = self._edi_update_state_code(orig_vals)
        state = self.edi_find_state(code=state_code)
        self._edi_set_state(state)
        return state

    def _edi_update_state_code(self, orig_vals):
        state_code = self._edi_state_code_by_order_state()
        if state_code:
            return state_code
        satisfied = self._edi_compare_orig_values(orig_vals)
        state_code = self.EDI_STATE_ORDER_ACCEPTED
        if not satisfied:
            state_code = self.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        return state_code

    def _edi_state_code_by_order_state(self):
        return {
            "cancel": self.EDI_STATE_ORDER_REJECTED,
        }.get(self.state)

    def _edi_compare_orig_values(self, orig_vals):
        # ATM check only if lines have changes
        for rec in self.order_line:
            if rec.edi_state_id.code == self.EDI_STATE_ORDER_LINE_CHANGED:
                return False
        return True


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = [
        "sale.order.line",
        "edi.auto.exchange.consumer.mixin",
        "edi.id.mixin",
        "edi.state.consumer.mixin",
    ]

    def _edi_determine_lines_state(self, orig_vals):
        # Defaults
        state_code = self.order_id.EDI_STATE_ORDER_LINE_ACCEPTED
        state = self.edi_find_state(code=state_code)
        for line in self:
            if not line.edi_exchange_ready:
                continue
            satisfied = line._edi_compare_orig_values(orig_vals)
            if not satisfied:
                state_code = self.order_id.EDI_STATE_ORDER_LINE_CHANGED
                state = self.edi_find_state(code=state_code)
            line._edi_set_state(state)
        return state

    def _edi_compare_orig_values(self, vals_by_edi_id):
        qty_ok = True
        prod_ok = True
        vals = vals_by_edi_id.get(self.edi_id)
        if not vals:
            # TODO: a new line? What do we do?
            return True
        if self.product_uom_qty < vals["product_uom_qty"]:
            qty_ok = False
        if self.product_id.id != vals["product_id"]:
            prod_ok = False
        return qty_ok and prod_ok
