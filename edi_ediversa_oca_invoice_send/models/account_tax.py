# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    ediversa_tax_type = fields.Selection(selection="_get_ediversa_tax_type_option")

    @api.model
    def _get_ediversa_tax_type_option(self):
        return [
            ("VAT", _("VAT")),
            ("IGI", _("IGIC")),
            ("EXT", _("Tax Exempt")),
            ("RE", _("Equivalence Surcharge")),
            ("ACT", _("Alcohol Taxes")),
            ("ENV", _("Green Point")),
            ("RET", _("Withholdings For Professional Services")),
        ]
