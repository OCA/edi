# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.account_payment_unece.tests.test_account_invoice import \
    TestAccountInvoice
from facturx import get_facturx_xml_from_pdf, check_facturx_xsd


class TestFacturXInvoice(TestAccountInvoice):

    def test_deep_customer_invoice(self):
        invoice = self.test_only_create_invoice()
        pdf_content = self.env['report'].get_pdf(
            [invoice.id], 'account.report_invoice')
        res = get_facturx_xml_from_pdf(pdf_content, check_xsd=True)
        self.assertTrue(res[0], 'factur-x.xml')
        self.assertTrue(check_facturx_xsd(res[1]))
