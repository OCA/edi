# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_payment_unece.tests.test_account_invoice import \
    TestAccountInvoice


class TestUblInvoice(TestAccountInvoice):

    def test_ubl_generate(self):
        ro = self.env['report']
        buo = self.env['base.ubl']
        invoice = self.test_only_create_invoice()
        for version in ['2.0', '2.1']:
            # I didn't manage to make it work with new api :-(
            pdf_file = ro.with_context(ubl_version=version).get_pdf(
                [invoice.id], 'account.report_invoice')
            res = buo.get_xml_files_from_pdf(pdf_file)
            invoice_filename = invoice.get_ubl_filename(version=version)
            self.assertTrue(invoice_filename in res)
