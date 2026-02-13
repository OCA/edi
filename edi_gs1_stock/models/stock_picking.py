# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models

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

    def _common_instruction(self, send, type_code):
        delivery = self
        edi_backend = self.get_backend_by_delivery()
        values = {"model": delivery._name, "res_id": delivery.id}
        exchange_record = edi_backend.create_record(type_code, values)
        edi_backend.exchange_generate(exchange_record)
        send = self.env.context.get("edi_exchange_send", send)
        if send:
            edi_backend.exchange_send(exchange_record)
        return exchange_record

    # TODO: check if sending is required
    def send_wh_inbound_instruction(self, send=False):
        """Generate an Inbound Instruction for given delivery and send it.
        """
        type_code = "warehousingInboundInstruction"
        return self._common_instruction(send, type_code)

    def action_send_wh_inbound_instruction(self):
        # TODO: return action compat dict
        return self.send_wh_inbound_instruction()

    def send_wh_outbound_instruction(self, send=False):
        """Generate an Outbound Instruction for given delivery and send it.
        """
        type_code = "warehousingOutboundInstruction"
        return self._common_instruction(send, type_code)

    def action_send_wh_outbound_instruction(self):
        # TODO: return action compat dict
        return self.send_wh_outbound_instruction()

    def action_stop_gs1(self):
        exchange_records = self.env["edi.exchange.record"].search(
            [("model", "=", self._name), ("res_id", "in", self.ids)]
        )
        if exchange_records:
            exchange_records.action_exchange_stop()
        return {}

    def unlink(self):
        """

        :return: bool
        """
        picking_ids = self.ids
        result = super().unlink()
        exchange_records = self.env["edi.exchange.record"].search(
            [("model", "=", self._name), ("res_id", "in", picking_ids)]
        )
        exchange_records.write({"model": False, "res_id": False})
        if exchange_records:
            exchange_records.action_exchange_stop()
        for exchange_record in exchange_records:
            exchange_record.message_post(body=_("Related picking deleted"))
        return result
