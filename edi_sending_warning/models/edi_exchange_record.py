# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiExchangeRecordListener(Component):
    _name = "edi.exchange.listener"
    _inherit = ["base.event.listener"]
    _apply_on = ["edi.exchange.record"]

    def on_record_write(self, record, fields=None):
        if (
            fields
            and "edi_exchange_state" in fields
            and record.edi_exchange_state == "output_error_on_send"
        ):
            record.record.sending_error_type = "edi_message_not_sent"
