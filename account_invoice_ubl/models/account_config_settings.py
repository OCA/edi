# -*- coding: utf-8 -*-
# © 2017 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    embed_pdf_in_ubl_xml_invoice = fields.Boolean(
        related='company_id.embed_pdf_in_ubl_xml_invoice')
