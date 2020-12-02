# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


# TODO: inherit from exchange consumer


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def get_backend_by_delivery(self):
        """Retrieve GS1 backend by given delivery order (stock.picking).

        You might have different LSP and pick up the right backend
        based on the delivery order.
        """
        # TODO: how do we handle this?
        # We could have a wizard of some special fields to set by record
        # which backend to use.
        return self.env.ref("edi_gs1.edi_backend_gs1_default")

    # TODO: check if sending is required
    def send_wh_inbound_instruction(self, send=False):
        """Generate an Inbound Instruction for given delivery and send it.
        """
        delivery = self
        edi_backend = self.get_backend_by_delivery()
        type_code = "warehousingInboundInstructionMessage"
        values = {"model": delivery._name, "res_id": delivery.id}
        exchange_record = edi_backend.create_record(type_code, values)
        edi_backend.generate_output(exchange_record)

        if "edi_exchange_send" in self.env.context:
            send = self.env.context.get("edi_exchange_send")
        if send:
            edi_backend.exchange_send(exchange_record)
        return exchange_record

    def action_send_wh_inbound_instruction(self):
        # TODO: return action compat dict
        return self.send_wh_inbound_instruction()

    def send_wh_outbound_instruction(self, send=False):
        """Generate an Outbound Instruction for given delivery and send it.
        """
        delivery = self
        edi_backend = self.get_backend_by_delivery()
        type_code = "warehousingOutboundInstructionMessage"
        values = {"model": delivery._name, "res_id": delivery.id}
        exchange_record = edi_backend.create_record(type_code, values)
        edi_backend.generate_output(exchange_record)

        if "edi_exchange_send" in self.env.context:
            send = self.env.context.get("edi_exchange_send")
        if send:
            edi_backend.exchange_send(exchange_record)
        return exchange_record

    def action_send_wh_outbound_instruction(self):
        # TODO: return action compat dict
        return self.send_wh_outbound_instruction()
