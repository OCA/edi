# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_document_from_attachment(self, attachment_ids=None):
        """Inherit native method used when clicking on the 'Upload' button from the
        Vendor Bill tree view"""
        if self:
            company_id = self.company_id.id
        else:
            company_id = self.env.company.id
        wiz = self.env["account.invoice.import"].create(
            {
                "company_id": company_id,
                "invoice_attachment_ids": [Command.set(attachment_ids)],
            }
        )
        action = wiz.import_invoices()
        return action
