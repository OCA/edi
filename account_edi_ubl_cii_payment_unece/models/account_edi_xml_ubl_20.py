# Copyright 2026  Akretion (https://www.akretion.com).
# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUbl_20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _import_fill_invoice_form(self, journal, tree, invoice, qty_factor):
        res = super()._import_fill_invoice_form(journal, tree, invoice, qty_factor)
        payment_mean_code = None
        for node in tree.findall("./{*}PaymentMeans/{*}PaymentMeansCode"):
            if note := node.text:
                payment_mean_code = note
                break
        if not payment_mean_code:
            return res
        # Look for a matching payment mode
        payment_mode = self.env["account.payment.mode"].search(
            [
                ("payment_type", "=", "outbound"),
                ("payment_method_id.unece_code", "=", payment_mean_code),
            ],
            limit=1,
        )
        if payment_mode:
            invoice.payment_mode_id = payment_mode
        return res
