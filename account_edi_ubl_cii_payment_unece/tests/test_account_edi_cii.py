# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

import lxml

from .common import CommonAccountEdiUnece


class TestAccountEdiCII(CommonAccountEdiUnece):
    def test_export_facturx(self):
        """Test export of UNECE payment mean code to FacturX XML file."""
        # Configure company
        self.env.company.write(
            {
                "country_id": self.env.ref("base.fr").id,
                "vat": "FR00000000000",
            }
        )
        # Configure payment method
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.inbound_payment_method.unece_id = unece
        # Configure partner
        self.partner.write(
            {
                "country_id": self.env.ref("base.fr").id,
                "invoice_edi_format": "facturx",
            }
        )
        # Create invoice
        invoice = self._create_out_invoice(post=True)
        self.assertTrue(invoice.preferred_payment_method_line_id)
        # Send it to generate its XML file
        wiz_send = (
            self.env["account.move.send.wizard"]
            .with_context(active_model=invoice._name, active_ids=invoice.ids)
            .create({})
        )
        wiz_send.action_send_and_print()
        # Check XML file content
        self.assertTrue(invoice.ubl_cii_xml_file)
        xml = base64.b64decode(invoice.ubl_cii_xml_file)
        root = lxml.etree.fromstring(xml)
        payment_means = root.find(".//{*}SpecifiedTradeSettlementPaymentMeans")
        self.assertTrue(len(payment_means))
        payment_means_code = payment_means.find("{*}TypeCode")
        self.assertTrue(payment_means_code is not None)
        self.assertEqual(payment_means_code.text, unece.code)

    def test_export_zugferd(self):
        """Test export of UNECE payment mean code to ZUGFeRD XML file."""
        # Configure company
        self.env.company.write(
            {
                "country_id": self.env.ref("base.de").id,
                "vat": "DE00000000000",
            }
        )
        # Configure payment method
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.inbound_payment_method.unece_id = unece
        # Configure partner
        self.partner.write(
            {
                "country_id": self.env.ref("base.de").id,
                "invoice_edi_format": "zugferd",
            }
        )
        # Create invoice
        invoice = self._create_out_invoice(post=True)
        self.assertTrue(invoice.preferred_payment_method_line_id)
        # Send it to generate its XML file
        wiz_send = (
            self.env["account.move.send.wizard"]
            .with_context(active_model=invoice._name, active_ids=invoice.ids)
            .create({})
        )
        wiz_send.action_send_and_print()
        # Check XML file content
        self.assertTrue(invoice.ubl_cii_xml_file)
        xml = base64.b64decode(invoice.ubl_cii_xml_file)
        root = lxml.etree.fromstring(xml)
        payment_means = root.find(".//{*}SpecifiedTradeSettlementPaymentMeans")
        self.assertTrue(len(payment_means))
        payment_means_code = payment_means.find("{*}TypeCode")
        self.assertTrue(payment_means_code is not None)
        self.assertEqual(payment_means_code.text, unece.code)

    def test_import_facturx(self):
        """Test import of UNECE payment mean code from FacturX XML file."""
        # Configure payment method
        unece = self.env.ref("account_payment_unece.payment_means_31")
        self.outbound_payment_method.unece_id = unece
        # Create a draft invoice (current partner will be overridden)
        invoice = self._create_in_invoice()
        # Import the XML invoice file containing the expected UNECE payment mean code
        file_path = (
            "account_edi_ubl_cii_payment_unece/"
            "tests/test_files/test_import_invoice_facturx.xml"
        )
        self._import_invoice_xml_file(invoice, file_path)
        # Check payment method
        payment_method = invoice.preferred_payment_method_line_id.payment_method_id
        self.assertEqual(payment_method.unece_id, unece)
        self.assertEqual(payment_method, self.outbound_payment_method)
