# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_edi_decoder(self, file_data, new=False):
        if file_data["type"] == "pdf":
            return self.env[
                "baseimportpdfbytemplate.account.mixin"
            ]._import_invoice_base_import_pdf_by_template
        return super()._get_edi_decoder(file_data, new=new)
