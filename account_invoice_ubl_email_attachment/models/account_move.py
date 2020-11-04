# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_sent(self):
        action = super().action_invoice_sent()
        if self.company_id.include_ubl_attachment_in_invoice_email:
            action["context"]["attach_ubl_xml_file"] = True
        return action

    def _generate_email_ubl_attachment(self):
        self.ensure_one()
        if not self.is_ubl_sale_invoice_posted():
            return self.env["ir.attachment"]
        version = self.get_ubl_version()
        xml_filename = self.get_ubl_filename(version=version)
        xml_string = self.generate_ubl_xml_string(version=version)
        return (
            self.env["ir.attachment"]
            .with_context({})
            .create(
                {
                    "name": xml_filename,
                    "res_model": str(self._name),
                    "res_id": self.id,
                    "datas": base64.b64encode(xml_string),
                    "type": "binary",
                }
            )
        )
