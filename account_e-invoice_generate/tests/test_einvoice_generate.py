# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestEInvoiceGenerate(TransactionCase):
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
