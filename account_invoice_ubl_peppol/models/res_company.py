# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import sys

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

DEFAULT_DOMAIN_PEPPOL = "[]"


class ResCompany(models.Model):
    _inherit = "res.company"

    ubl_domain_peppol = fields.Text(
        string="PEPPOL domain",
        default=DEFAULT_DOMAIN_PEPPOL,
        help="Use this domain to determine which UBL invoices should "
        "have PEPPOL dialect.",
    )
    ubl_default_tax = fields.Many2one(
        comodel_name="account.tax",
        string="Default tax",
        help="According to PEPPOL BR-CO-18, an invoice must always have a tax "
        "subtotal, but for example non-profits are exempt from charging VAT. "
        "With this option you can choose a default tax to use.",
    )
    ubl_default_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Default UoM",
        help="Use this unit if an invoice line has no unit or product unit",
    )

    def get_ubl_domain_peppol(self):
        return safe_eval(self.ubl_domain_peppol) if self.ubl_domain_peppol else []

    @api.constrains("ubl_domain_peppol")
    def _check_ubl_domain_peppol(self):
        try:
            domain = self.get_ubl_domain_peppol()
            self.env["account.move"].search_count(domain)
        except:  # noqa
            raise ValidationError(
                _("Not a valid domain: {}: {}").format(
                    sys.exc_info()[0].__name__, sys.exc_info()[1]
                )
            )
