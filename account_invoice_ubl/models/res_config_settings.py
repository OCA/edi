# Copyright 2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    embed_pdf_in_ubl_xml_invoice = fields.Boolean(
        related="company_id.embed_pdf_in_ubl_xml_invoice", readonly=False
    )
