# Copyright 2015-2021 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import is_html_empty


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_import_warnings = fields.Html(readonly=True)
    show_invoice_import_warnings = fields.Boolean(
        compute="_compute_show_invoice_import_warnings"
    )

    @api.depends("state", "invoice_import_warnings")
    def _compute_show_invoice_import_warnings(self):
        for move in self:
            show = False
            if move.state == "draft" and not is_html_empty(
                move.invoice_import_warnings
            ):
                show = True
            move.show_invoice_import_warnings = show
