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
    # Line states that make the order not fully accepted
    EDI_STATE_ORDER_LINE_ALTERED_STATES = (
        EDI_STATE_ORDER_LINE_ADDED,
        EDI_STATE_ORDER_LINE_CHANGED,
        EDI_STATE_ORDER_LINE_NOT_ACCEPTED,
    )

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
            if rec.edi_state_id.code in self.EDI_STATE_ORDER_LINE_ALTERED_STATES:
                return False
        return True

    def create(self, vals):
        # Inject a key to check if we are in a SO create session
        # to not mess up w/ lines when not needed.
        # The key is removed right aftewards.
        return (
            super(SaleOrder, self.with_context(evt_from_create=self._name))
            .create(vals)
            .with_context(evt_from_create=None)
        )


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
        for line in self:
            if not line.edi_exchange_ready:
                continue
            state_code = line._edi_get_line_state_code(orig_vals)
            state = self.edi_find_state(code=state_code)
            line._edi_set_state(state)

    def _edi_get_line_state_code(self, vals_by_edi_id):
        vals = vals_by_edi_id.get(self.edi_id)
        if not vals:
            # Brand new line
            return self.order_id.EDI_STATE_ORDER_LINE_ADDED
        if not self.product_uom_qty:
            return self.order_id.EDI_STATE_ORDER_LINE_NOT_ACCEPTED
        if self.product_uom_qty < vals["product_uom_qty"]:
            return self.order_id.EDI_STATE_ORDER_LINE_CHANGED
        if self.product_id.id != vals["product_id"]:
            return self.order_id.EDI_STATE_ORDER_LINE_CHANGED
        return self.order_id.EDI_STATE_ORDER_LINE_ACCEPTED
