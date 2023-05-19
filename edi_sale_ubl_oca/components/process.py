# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__file__)


class EDIExchangeSOInput(Component):

    _inherit = "edi.input.sale.order.process"

    def _handle_create_order(self, order_id):
        order = super()._handle_create_order(order_id)
        if self._is_ubl_exchange():
            state = order._edi_update_state()
            if state:
                order._edi_set_state(state)
                return order
            self._handle_create_order_no_state()
        return order

    def _is_ubl_exchange(self):
        return self.exchange_record.type_id.backend_type_id == self.env.ref(
            "edi_ubl_oca.edi_backend_type_ubl"
        )

    def _handle_create_order_no_state(self):
        msg = "Cannot determine EDI state"
        if not self.exchange_record.type_id.state_workflow_ids:
            msg += (
                f". No workflow configured on exc type "
                f"'{self.exchange_record.type_id.name}'"
            )
        _logger.error(msg)
