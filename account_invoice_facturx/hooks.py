# Copyright 2018-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def set_xml_format_in_pdf_invoice_to_facturx(env):
    companies = env["res.company"].search(
        [("xml_format_in_pdf_invoice", "in", (False, "none"))]
    )
    companies.write({"xml_format_in_pdf_invoice": "factur-x"})
