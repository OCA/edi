# Copyright 2015-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from facturx import get_facturx_level
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

RAM_NS = (
    "urn:un:unece:uncefact:data:standard:"
    "ReusableAggregateBusinessInformationEntity:100"
)
NSMAP = {"ram": RAM_NS}


class TestFacturXInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.product1 = cls.env.ref("product.product_product_4")
        cls.product2 = cls.env.ref("product.product_product_1")
        cls.env.user.partner_id.email = "billing@example.com"
        cls.proprietary_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "acc_number": "ACC-FACTURX-0001",
                "acc_type": "bank",
            }
        )
        sale_taxes = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "sale"),
                "|",
                ("unece_type_id", "=", False),
                ("unece_categ_id", "=", False),
            ]
        )
        sale_taxes.write(
            {
                "unece_type_id": cls.env.ref("account_tax_unece.tax_type_vat").id,
                "unece_categ_id": cls.env.ref("account_tax_unece.tax_categ_s").id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "move_type": "out_invoice",
                "partner_id": cls.env.ref("base.res_partner_2").id,
                "currency_id": cls.company.currency_id.id,
                "partner_bank_id": cls.proprietary_bank.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product1.id,
                            "quantity": 12,
                            "price_unit": 42.42,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product2.id,
                            "quantity": 2,
                            "price_unit": 12.34,
                        },
                    ),
                ],
            }
        )
        cls.invoice.action_post()
        cls.invoice.partner_bank_id = cls.proprietary_bank

    def _generate_xml_root(self, invoice=None, level="en16931"):
        invoice = invoice or self.invoice
        self.company.write({"facturx_level": level})
        xml_bytes, fx_level = invoice.generate_facturx_xml()
        self.assertEqual(fx_level, level)
        return etree.fromstring(xml_bytes)

    def test_deep_customer_invoice(self):
        # Bug in Basic XSD: missing CountrySubDivisionName
        # I reported it to FNFE-MPE on 24/10/2021
        # In the meantime, we want to avoid the bug:
        self.company.partner_id.state_id = False
        self.invoice.partner_id.state_id = False
        if self.company.xml_format_in_pdf_invoice != "factur-x":
            self.company.write({"xml_format_in_pdf_invoice": "factur-x"})
        # inv_report = self.env.ref("account.account_invoices").with_context(
        #    force_report_rendering=True
        # )
        for level in ["minimum", "basicwl", "basic", "en16931", "extended"]:
            self.company.write({"facturx_level": level})
            # Travis tests get stalled on this line
            # Maybe it's not possible to render a PDF on Travis... I don't know
            # pdf_content, pdf_ext = inv_report._render_qweb_pdf(
            #    res_ids=[self.invoice.id]
            # )
            # xml_filename, xml_string = get_facturx_xml_from_pdf(
            #    pdf_content, check_xsd=True
            # )
            # self.assertTrue(xml_filename, "factur-x.xml")
            # xml_root = etree.fromstring(xml_string)
            # facturx_level = get_facturx_level(xml_root)
            # self.assertEqual(facturx_level, level)
            xml_bytes, fx_level = self.invoice.generate_facturx_xml()
            self.assertEqual(fx_level, level)
            xml_root = etree.fromstring(xml_bytes)
            facturx_level = get_facturx_level(xml_root)
            self.assertEqual(facturx_level, level)

    def test_email_uriid_has_no_schemeid(self):
        xml_root = self._generate_xml_root(level="en16931")
        uriid_nodes = xml_root.xpath(
            "//ram:DefinedTradeContact/"
            "ram:EmailURIUniversalCommunication/"
            "ram:URIID",
            namespaces=NSMAP,
        )
        self.assertTrue(uriid_nodes, "Expected seller email URIID in EN16931 XML")
        self.assertEqual(uriid_nodes[0].text, "billing@example.com")
        self.assertNotIn("schemeID", uriid_nodes[0].attrib)

    def test_credit_transfer_uses_proprietary_id_for_non_iban_account(self):
        xml_root = self._generate_xml_root(level="en16931")
        proprietary_nodes = xml_root.xpath(
            "//ram:SpecifiedTradeSettlementPaymentMeans/"
            "ram:PayeePartyCreditorFinancialAccount/"
            "ram:ProprietaryID",
            namespaces=NSMAP,
        )
        iban_nodes = xml_root.xpath(
            "//ram:SpecifiedTradeSettlementPaymentMeans/"
            "ram:PayeePartyCreditorFinancialAccount/"
            "ram:IBANID",
            namespaces=NSMAP,
        )

        self.assertTrue(
            proprietary_nodes,
            "Expected ProprietaryID for non-IBAN creditor account",
        )
        self.assertEqual(
            proprietary_nodes[0].text,
            self.proprietary_bank.sanitized_acc_number,
        )
        self.assertFalse(iban_nodes, "IBANID should not be generated for non-IBAN bank")

    def test_credit_transfer_requires_account_identifier(self):
        invoice = self.invoice.copy(default={"partner_bank_id": False})
        invoice.action_post()

        self.company.write({"facturx_level": "en16931"})
        with patch(
            "odoo.addons.account_invoice_facturx.models.account_move.xml_check_xsd"
        ) as xml_check_xsd:
            with self.assertRaises(UserError):
                invoice.generate_facturx_xml()
            xml_check_xsd.assert_not_called()
