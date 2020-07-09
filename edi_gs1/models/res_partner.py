# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # TODO: move to another module? Or, is there another module providing this?
    gln_code = fields.Char()
    is_lsp = fields.Boolean(string="Is Logistic Services Provider (LSP)")
