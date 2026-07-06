# Copyright 2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def set_xml_format_in_pdf_invoice_to_ubl(cr, registry=None):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    companies.write({"xml_format_in_pdf_invoice": "ubl"})

    companies = env["res.company"].search(
        [("xml_format_in_pdf_invoice", "in", (False, "none"))]
    )
    companies.write({"xml_format_in_pdf_invoice": "factur-x"})


def remove_ubl_xml_format_in_pdf_invoice(cr, registry=None):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
    companies.write({"xml_format_in_pdf_invoice": "none"})
