# Copyright 2020 Sunflower IT <info@sunflowerweb.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ubl_default_tax = fields.Many2one(
        comodel_name="account.tax",
        string="Use this tax as a 0.0 tax if an invoice has no taxes",
        help="According to PEPPOL BR-CO-18, an invoice must always have a tax "
        "subtotal, but for example non-profits are exempt from charging VAT. "
        "With this option you can choose a default tax to use.")
