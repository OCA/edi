# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoiceSend(models.TransientModel):
    _inherit = "account.invoice.send"

    def send_mail(self):
        return self.composer_id.send_mail()
