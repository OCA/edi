# Copyright 2023 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    ids_name = fields.Char(
        "IDS name", help="Code of this UOM according to the IDS protocol."
    )
    ids_name_alternative = fields.Char(
        "Alternative IDS name",
        help="If you encounter webshops using wrong "
        "UOM names for IDS, fill them in here, separated by spaces",
    )
