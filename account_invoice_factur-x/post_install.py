# -*- coding: utf-8 -*-
# © 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def set_xml_format_in_pdf_invoice_to_facturx(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        companies = env['res.company'].search([])
        companies.write({'xml_format_in_pdf_invoice': 'factur-x'})
    return
