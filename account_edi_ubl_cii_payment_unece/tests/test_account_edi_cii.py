# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from .common import CommonAccountEdiUnece


class TestAccountEdiCII(CommonAccountEdiUnece):
    def test_import_facturx(self):
        """Test import of UNECE payment mean code from FacturX XML file."""
        # Configure payment method
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.outbound_payment_method.unece_id = unece
        # Create a draft invoice (current partner will be overridden)
        # Import the XML invoice file containing the expected UNECE payment mean code
        file_path = (
            "account_edi_ubl_cii_payment_unece/"
            "tests/test_files/test_import_invoice_facturx.xml"
        )
        invoice = self._import_invoice_xml_file(
            self.company_data["default_journal_purchase"], file_path
        )
        # Check payment method
        payment_method = invoice.payment_mode_id.payment_method_id
        self.assertEqual(payment_method.unece_id, unece)
        self.assertEqual(payment_method, self.outbound_payment_method)

    def test_import_facturx_uses_payment_mode_from_invoice_company(self):
        """test import only uses payment mode from invoice company"""
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.outbound_payment_method.unece_id = unece
        other_company_payment_mode = self._create_other_company_payment_mode(
            self.outbound_payment_method
        )
        file_path = (
            "account_edi_ubl_cii_payment_unece/"
            "tests/test_files/test_import_invoice_facturx.xml"
        )
        invoice = self._import_invoice_xml_file(
            self.company_data["default_journal_purchase"], file_path
        )
        self.assertNotEqual(invoice.payment_mode_id, other_company_payment_mode)
        self.assertEqual(invoice.payment_mode_id, self.outbound_payment_mode)
