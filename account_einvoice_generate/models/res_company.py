# Copyright 2018-2021 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        [("none", "None")], string="XML Format embedded in PDF invoice"
    )
