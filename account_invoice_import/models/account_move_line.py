# Copyright 2026 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # I initially wanted to name this field import_identifier
    # but the risk of naming conflict was too high, so I decided to
    # set a longer name
    import_invoice_line_identifier = fields.Char(
        string="Import Identifier",
        readonly=True,
        help="When importing a vendor bill, this field stores BT-126",
    )
