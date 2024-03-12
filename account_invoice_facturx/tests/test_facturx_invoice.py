# Copyright 2015-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from facturx import get_facturx_level
from lxml import etree

from odoo.tests.common import TransactionCase


class TestFacturXInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.product1 = cls.env.ref("product.product_product_4")
        cls.product2 = cls.env.ref("product.product_product_1")
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
