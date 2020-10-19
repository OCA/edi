# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "edi.document.mixin"]

    def get_edi_mail_file_action(self):
        return self.env.ref("account.account_invoices")

    def _expected_edi_documents(self):
        if self.state == "draft":
            return self.env["edi.format"]
        result = super(AccountMove, self)._expected_edi_documents()
        result |= self.commercial_partner_id.account_move_edi_format_ids
        result |= self.journal_id.account_move_edi_format_ids
        return result.filtered(lambda r: r.can_send)

    def _send_edi_mail_wizard(self):
        action = self.action_invoice_sent()
        action["context"]["active_ids"] = self.ids
        return action

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, *args, **kwargs):
        result = super().message_post(*args, **kwargs)
        if self.env.context.get("edi_document_id", False):
            result.res_id = self.env.context.get("edi_document_id")
            result.model = "edi.document"
        return result
