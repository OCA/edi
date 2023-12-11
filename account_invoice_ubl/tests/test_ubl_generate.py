# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_payment_unece.tests.test_account_invoice import \
    TestAccountInvoice


class TestUblInvoice(TestAccountInvoice):

    def test_ubl_generate(self):
        ro = self.env.ref('account.account_invoices')
        buo = self.env['base.ubl']
        invoice = self.test_only_create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != 'ubl':
            invoice.company_id.xml_format_in_pdf_invoice = 'ubl'
        for version in ['2.0', '2.1']:
            pdf_file = ro.with_context(ubl_version=version).render_qweb_pdf(
                invoice.ids)[0]
            res = buo.get_xml_files_from_pdf(pdf_file)
            invoice_filename = invoice.get_ubl_filename(version=version)
            self.assertTrue(invoice_filename in res)
