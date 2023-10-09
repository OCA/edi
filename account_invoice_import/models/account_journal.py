# Copyright 2023 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_invoice_from_attachment(self, attachment_ids=None):
        if self._context.get("force_native_invoice_import") or not attachment_ids:
            return super().create_invoice_from_attachment(attachment_ids=attachment_ids)
        attachment = self.env["ir.attachment"].browse(attachment_ids[0])
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": attachment.datas,
                "invoice_filename": attachment.name,
            }
        )
        action = wiz.import_invoice()
        # JS crash when there is not a 'views' key != False
        if (
            not action.get("views")
            and action.get("view_mode")
            and action["view_mode"].startswith("form")
        ):
            action["views"] = [(False, "form")]
        return action
