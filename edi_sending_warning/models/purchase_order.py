# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sending_error_type = fields.Selection(
        selection_add=[("edi_message_not_sent", "EDI Message not sent")],
    )

    @api.depends("sending_error_type")
    def _compute_transmission_error(self):
        super()._compute_transmission_error()
        for rec in self:
            if (
                not rec.transmission_error
                and rec.exchange_record_ids
                and any(
                    x.edi_exchange_state == "output_error_on_send"
                    for x in rec.exchange_record_ids
                )
            ):
                rec.transmission_error = (
                    rec.sending_error_type == "edi_message_not_sent"
                )
