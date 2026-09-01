# Copyright 2025 Akretion France (https://www.akretion.com/)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_document_from_attachment(self, attachment_ids):
        """Inherit native method used when clicking on the 'Upload' button from the
        Vendor Bill tree view"""
        MOVE = self.env["account.move"]
        attachment_ids_by_odoo = []
        attachment_ids_by_oca = []
        attachments = self.env["ir.attachment"].browse(attachment_ids)
        for attachment in attachments:
            to_process = attachment._unwrap_edi_attachments()
            decoder = False
            for file_data in to_process:
                decoder = MOVE._get_edi_decoder(file_data)
                if decoder:
                    attachment_ids_by_odoo.append(attachment.id)
                    break
            if not decoder:
                attachment_ids_by_oca.append(attachment.id)
        move_ids = []
        if attachment_ids_by_odoo:
            res = super().create_document_from_attachment(attachment_ids_by_odoo)
            if not attachment_ids_by_oca:
                return res
            move_ids = res["domain"][0][2]
        if attachment_ids_by_oca:
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
            if not attachment_ids_by_odoo:
                return action
            next_action = action["params"]["next"]
            move_id = next_action.get("res_id")
            if move_id:
                move_ids.append(move_id)
            else:
                move_ids += next_action["domain"][0][2]
            new_next_action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_in_invoice_type"
            )
            new_next_action["domain"] = [("id", "in", move_ids)]
            action["params"]["next"] = new_next_action
        return action
