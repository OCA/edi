# Copyright 2015-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.account_tax_unece.tests.test_account_invoice import \
    TestAccountInvoice
from facturx import get_facturx_xml_from_pdf, get_facturx_level
from lxml import etree


class TestFacturXInvoice(TestAccountInvoice):

    def test_deep_customer_invoice(self):
        invoice = self.test_only_create_invoice()
        company = invoice.company_id
        if company.xml_format_in_pdf_invoice != 'factur-x':
            company.xml_format_in_pdf_invoice = 'factur-x'
        inv_report = self.env.ref('account.account_invoices').with_context(
            force_report_rendering=True)
        for level in ['minimum', 'basicwl', 'basic', 'en16931', 'extended']:
            company.facturx_level = level
            pdf_content, pdf_ext = inv_report.render_qweb_pdf(
                res_ids=[invoice.id])
            xml_filename, xml_string = get_facturx_xml_from_pdf(
                pdf_content, check_xsd=True)
            self.assertTrue(xml_filename, 'factur-x.xml')
            xml_root = etree.fromstring(xml_string)
            facturx_level = get_facturx_level(xml_root)
            self.assertEqual(facturx_level, level)
