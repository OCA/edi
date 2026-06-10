# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from .common import CommonAccountEdiUnece


class TestAccountEdiUBLBIS3(CommonAccountEdiUnece):
    def test_import_ubl_bis3(self):
        """Test import of UNECE payment mean code from BIS3 XML file."""
        # Configure payment method
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.outbound_payment_method.unece_id = unece
        # Import the XML invoice file containing the expected UNECE payment mean code
        file_path = (
            "account_edi_ubl_cii_payment_unece/"
            "tests/test_files/test_import_invoice_ubl_bis3.xml"
        )
        invoice = self._import_invoice_xml_file(
            self.company_data["default_journal_purchase"], file_path
        )
        # Check payment method
        payment_method = invoice.payment_mode_id.payment_method_id
        self.assertEqual(payment_method.unece_id, unece)
        self.assertEqual(payment_method, self.outbound_payment_method)
