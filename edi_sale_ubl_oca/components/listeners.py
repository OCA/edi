# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__file__)


class EDISOEventListener(Component):
    _name = "edi.sale.order.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["sale.order"]

    @skip_if(lambda self, record, **kw: self._skip_state_update(record, **kw))
    def on_record_create(self, record, fields=None):
        self._handle_order_state(record.with_context(edi_sale_skip_state_update=True))

    @skip_if(lambda self, record, **kw: self._skip_state_update(record, **kw))
    def on_record_write(self, record, fields=None):
        self._handle_order_state(record.with_context(edi_sale_skip_state_update=True))

    # TODO: what to do?
    # def on_record_unlink(self, record):

    def _handle_order_state(self, order):
        state = order._edi_update_state()
        if not state:
            self._handle_order_state_no_state(order)

    def _skip_state_update(self, record, fields=None):
        if record.env.context.get("edi_sale_skip_state_update"):
            return True
        fields = fields or []
        return "state" not in fields and not self._is_ubl_exchange(record)

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
