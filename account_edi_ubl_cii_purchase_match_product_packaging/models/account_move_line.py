# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _set_product(self, product):
        self.ensure_one()
        res = super()._set_product(product)

        if self.ubl_unece_unit_code:
            if not self.env[
                "account.edi.xml.ubl_20"
            ]._import_fill_invoice_line_packaging(self):
                self.env["account.edi.xml.ubl_20"]._import_fill_invoice_line_uom(self)
        return res
