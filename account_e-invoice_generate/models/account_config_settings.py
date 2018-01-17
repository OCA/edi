# -*- coding: utf-8 -*-
# © 2018 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    xml_format_in_pdf_invoice = fields.Selection(
        related='company_id.xml_format_in_pdf_invoice')
