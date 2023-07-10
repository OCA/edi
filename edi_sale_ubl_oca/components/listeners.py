# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent, Component

_logger = logging.getLogger(__file__)


class EDISOEventListenerMixin(AbstractComponent):
    _name = "edi.sale.order.event.listener.mixin"
    _inherit = "base.event.listener"
    _apply_on = ["sale.order", "sale.order.line"]

    def on_record_create(self, record, fields=None):
        self._on_record_operation(record, fields=fields, operation="create")

    def on_record_write(self, record, fields=None):
        self._on_record_operation(record, fields=fields, operation="write")

    def _on_record_operation(self, record, fields=None, operation=None):
        if self._skip_state_update(record, fields=fields, operation=operation):
            return
        order, lines = self._get_records(record)
        order = order.with_context(edi_sale_skip_state_update=True)
        lines = lines.with_context(edi_sale_skip_state_update=True)
        self._handle_order_state(order, lines=lines)

    # TODO: what to do?
    # def on_record_unlink(self, record):

    def _get_records(self, record):
        raise NotImplementedError()

    def _handle_order_state(self, order, lines=None):
        state = order._edi_update_state(lines=lines)
        if not state:
            self._handle_order_state_no_state(order)

    def _skip_state_update(self, record, fields=None, operation=None):
        if record.env.context.get(
            "edi_sale_skip_state_update"
        ) or not self._is_ubl_exchange(record):
            return True
        return False

    def _is_ubl_exchange(self, record):
        return record.origin_exchange_type_id.backend_type_id == self.env.ref(
            "edi_ubl_oca.edi_backend_type_ubl"
        )

    def _handle_order_state_no_state(self, order):
        msg = "Cannot determine EDI state for order %(order_name)s"
        msg_args = dict(order_name=order.name)
        exc_type = order.origin_exchange_type_id
        if not exc_type.state_workflow_ids:
            msg += ". No workflow configured on exc type " "%(type_name)s'"
            msg_args["type_name"] = exc_type.name
        _logger.error(msg, msg_args)


class EDISOEventListener(Component):
    _name = "edi.sale.order.event.listener"
    _inherit = "edi.sale.order.event.listener.mixin"
    _apply_on = ["sale.order"]

    def _get_records(self, record):
        return record, record.order_line

    def _skip_state_update(self, record, fields=None, operation=None):
        res = super()._skip_state_update(record, fields=fields, operation=operation)
        if res:
            return res
        fields = fields or []
        # EDI state will be recomputed only at state change on write or in any case at creation
        skip = operation == "write" and (
            "state" not in fields or fields == ["edi_state_id"]
        )
        return skip


class EDISOLineEventListener(Component):
    _name = "edi.sale.order.line.event.listener"
    _inherit = "edi.sale.order.event.listener.mixin"
    _apply_on = ["sale.order.line"]

    def _get_records(self, record):
        return record.order_id, record

    def _skip_state_update(self, record, fields=None, operation=None):
        res = super()._skip_state_update(record, fields=fields, operation=operation)
        if res:
            return res
        if self.env.context.get("evt_from_create") == "sale.order":
            # If lines are created from an SO creation straight
            # bypass check and state compute because it will be done anyway at create.
            return True
        fields = fields or []
        # EDI state will be recomputed when critical line info has changed
        # TODO: tie this list w/ the fields in `s.o.l._edi_compare_orig_values`
        trigger_fields = ("product_id", "product_uom_qty")
        for fname in trigger_fields:
            if fname in fields:
                return False
