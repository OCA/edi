# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_order_ubl_import_http_confirmed = fields.Boolean(
        string="UBL order imported through HTTP set as confirmed",
        help="When set the UBL sales order imported through HTTP "
        "will be set as confirmed. Otherwise they are kept as draft.",
    )
