# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    include_ubl_attachment_in_invoice_email = fields.Boolean(
        string="Include UBL XML in Invoice Email",
        help="If active, the UBL Invoice XML file will be included "
        "in the attachments when sending the invoice by email.",
    )
