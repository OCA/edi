# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# @author: Lois Rilo <lois.rilo@forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EDIExchangeSOInput(Component):
    """Process Invoices (journal entries)."""

    _name = "edi.input.account.invoice.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.account.invoice"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.settings = self.type_settings.get("account_invoice_import", {})

    def process(self):
        wiz = self._setup_wizard()
        res = wiz.import_invoice()
        if wiz.state == "update" and wiz.invoice_id:
            invoice = wiz.invoice_id
            msg = _("Invoice has already been imported before")
            self._handle_existing_invoice(invoice, msg)
            raise UserError(msg)
        else:
            invoice_id = res["res_id"]
            invoice = self.env["account.move"].browse(invoice_id)
            if self._invoice_should_be_posted():
                invoice.action_post()
            self.exchange_record.sudo()._set_related_record(invoice)
            return _("Invoice %s created") % invoice.name
        raise UserError(_("Something went wrong with the importing wizard."))

    def _setup_wizard(self):
        """Init a `account.invoice.import` instance for current record."""
        ctx = self.settings.get("wiz_ctx", {})
        wiz = self.env["account.invoice.import"].with_context(**ctx).sudo().create({})
        wiz.invoice_file = self.exchange_record._get_file_content(binary=False)
        wiz.invoice_filename = self.exchange_record.exchange_filename
        return wiz

    def _invoice_should_be_posted(self):
        return self.settings.get("post_invoice", False)

    def _handle_existing_invoice(self, invoice, message):
        prev_record = self._get_previous_record(invoice)
        self.exchange_record.message_post_with_view(
            "edi_account_invoice_import.message_already_imported",
            values={
                "invoice": invoice,
                "prev_record": prev_record,
                "message": message,
                "level": "info",
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _get_previous_record(self, invoice):
        return self.env["edi.exchange.record"].search(
            [("model", "=", "account.move"), ("res_id", "=", invoice.id)], limit=1
        )
