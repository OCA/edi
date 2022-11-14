from odoo import _

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
        statement_id = res["res_id"]
        statement = self.env["account.bank.statement"].browse(statement_id)
        self.exchange_record.sudo()._set_related_record(statement)
        return _("Account Statement %s created") % statement.name
        # raise UserError(_("Something went wrong with the importing wizard."))

    def _setup_wizard(self):
        """Init a `account.statement.import` instance for current record."""
        ctx = self.settings.get("wiz_ctx", {})
        wiz = self.env["account.statement.import"].with_context(**ctx).sudo().create({})
        wiz.statement_file = self.exchange_record._get_file_content(binary=False)
        wiz.statement_filename = self.exchange_record.exchange_filename
        return wiz
