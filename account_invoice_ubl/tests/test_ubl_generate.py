# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_tax_unece.tests.test_account_invoice import TestAccountInvoice

from ..hooks import (
    remove_ubl_xml_format_in_pdf_invoice,
    set_xml_format_in_pdf_invoice_to_ubl,
)


class TestUblInvoice(TestAccountInvoice):
    def test_ubl_generate(self):
        invoice = self.test_only_create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != "ubl":
            invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        for version in ["2.0", "2.1"]:
            pdf_file = (
                self.env.ref("account.account_invoices")
                .with_context(ubl_version=version, force_report_rendering=True)
                .render_qweb_pdf(invoice.ids)[0]
            )
            res = self.env["base.ubl"].get_xml_files_from_pdf(pdf_file)
            invoice_filename = invoice.get_ubl_filename(version=version)
            self.assertTrue(invoice_filename in res)

    def test_attach_ubl_xml_file_button(self):
        invoice = self.test_only_create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != "ubl":
            invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        self.assertFalse(invoice.company_id.embed_pdf_in_ubl_xml_invoice)
        action = invoice.attach_ubl_xml_file_button()
        self.assertEqual(action["res_model"], "ir.attachment")
        self.assertEqual(action["view_mode"], "form,tree")
        self.assertFalse(action["views"])
        invoice.company_id.embed_pdf_in_ubl_xml_invoice = True
        action = invoice.attach_ubl_xml_file_button()
        self.assertEqual(action["res_model"], "ir.attachment")
        self.assertEqual(action["view_mode"], "form,tree")
        self.assertFalse(action["views"])

    def test_install_uninstall_hooks(self):
        set_xml_format_in_pdf_invoice_to_ubl(self.env.cr, None)
        self.assertTrue(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
        remove_ubl_xml_format_in_pdf_invoice(self.env.cr, None)
        self.assertFalse(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
        set_xml_format_in_pdf_invoice_to_ubl(self.env.cr, None)
        self.assertTrue(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
