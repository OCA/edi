# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from unittest.mock import patch

class TestEInvoiceGenerate(AccountTestInvoicingCommon):
    def test_config(self):
        """Test configuration of Electronic Invoices."""
        conf = self.env["res.config.settings"].create(
            {"xml_format_in_pdf_invoice": "none"}
        )
        conf.execute()
        self.assertTrue(self.env.company.xml_format_in_pdf_invoice)
        conf.xml_format_in_pdf_invoice = False
        conf.execute()
        self.assertFalse(self.env.company.xml_format_in_pdf_invoice)

    @patch('odoo.addons.account_einvoice_generate.models.res_company.ResCompany.xml_format_in_pdf_invoice', xml_format) #noqa
    def test_xml_format_in_pdf_invoice_true_answer(self):
        self.assertEquals(cls.invoice._xml_format_in_pdf_invoice, xml_format)

    @patch('odoo.addons.account_einvoice_generate.models.res_company.ResCompany.xml_format_in_pdf_invoice', "none") #noqa
    def test_xml_format_in_pdf_invoice_false_answer(self):
        self.assertFalse(cls.invoice._xml_format_in_pdf_invoice)

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.invoice = cls.init_invoice('out_invoice', products=cls.product_a+cls.product_b)
