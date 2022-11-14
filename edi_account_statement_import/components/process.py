from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EDIExchangeSOInput(Component):
    """Process account statement."""

    _name = "edi.input.account.statement.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.account.bank.statement"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.settings = self.type_settings.get("account_statement_import", {})

    def process(self):
        wiz = self._setup_wizard()
        res = wiz.import_file_button()
        account_statement = wiz.id
        statement_id = res["res_id"]
        statement = self.env["account.bank.statement"].browse(statement_id)
        self.exchange_record.sudo()._set_related_record(statement)
        return _("Account Statement %s created") % statement.name
        raise UserError(_("Something went wrong with the importing wizard."))

    def _setup_wizard(self):
        """Init a `account.statement.import` instance for current record."""
        ctx = self.settings.get("wiz_ctx", {})
        wiz = self.env["account.statement.import"].with_context(
            **ctx).sudo().create({})
        wiz.statement_file = self.exchange_record._get_file_content(
            binary=False)
        wiz.statement_filename = self.exchange_record.exchange_filename
        return wiz
    def _handle_existing_order(self, order, message):
    prev_record = self._get_previous_record(order)
    self.exchange_record.message_post_with_view(
          "edi_account_statement_import.message_already_imported",
       values={
	"order": order,
	"prev_record": prev_record,
	"message": message,
	"level": "info",
          },
       subtype_id=self.env.ref("mail.mt_note").id,
       )

    def _get_previous_record(self, order):
        return self.env["edi.exchange.record"].search(
            [("model", "=", "account.statement.import"), ("res_id", "=", order.id)], limit=1
        )
