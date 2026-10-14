# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_tax_unece.tests.test_account_invoice import TestAccountInvoice


class TestAccountInvoiceUblPeppol(TestAccountInvoice):
    def test_ubl_generate_peppol(self):
        invoice = self.test_only_create_invoice()
        invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        version = "2.1"
        pdf_file = (
            self.env.ref("account.account_invoices")
            .with_context(ubl_version=version, force_report_rendering=True)
            .render_qweb_pdf(invoice.ids)[0]
        )
        res = self.env["base.ubl"].get_xml_files_from_pdf(pdf_file)
        invoice_filename = invoice.get_ubl_filename(version=version)
        self.assertTrue(invoice_filename in res)
        # TODO: implement PEPPOL validation here
