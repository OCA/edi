# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.account_payment_unece.tests.test_account_invoice import \
    TestAccountInvoice
import PyPDF2
from lxml import etree
from StringIO import StringIO


class TestFacturXInvoice(TestAccountInvoice):

    def test_deep_customer_invoice(self):
        invoice = self.test_only_create_invoice()
        pdf_content = self.env['report'].get_pdf(
            [invoice.id], 'account.report_invoice')
        fd = StringIO(pdf_content)
        pdf = PyPDF2.PdfFileReader(fd)
        pdf_root = pdf.trailer['/Root']
        embeddedfile = pdf_root['/Names']['/EmbeddedFiles']['/Names']
        self.assertEquals(embeddedfile[0], 'ZUGFeRD-invoice.xml')
        zugferd_file_dict_obj = embeddedfile[1]
        zugferd_file_dict = zugferd_file_dict_obj.getObject()
        xml_string = zugferd_file_dict['/EF']['/F'].getData()
        xml_root = etree.fromstring(xml_string)
        self.assertTrue(xml_root.tag.startswith(
            '{urn:ferd:CrossIndustryDocument:invoice:1p0'))
