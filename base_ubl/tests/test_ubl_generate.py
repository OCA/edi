# Copyright 2019 Onestein (<https://www.onestein.eu>)
# © 2017-2020 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mimetypes
from io import BytesIO

from lxml import etree
from PyPDF2 import PdfFileReader

from odoo.exceptions import UserError
from odoo.tests.common import HttpCase
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestUblInvoice(AccountTestInvoicingCommon, HttpCase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Internal User",
                "login": "internal.user@test.odoo.com",
                "email": "internal.user@test.odoo.com",
                "groups_id": [
                    (6, 0, cls.env.user.groups_id.ids),
                    (4, cls.env.ref("account.group_account_user").id),
                ],
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.invoice_tax = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company_data["company"].id),
                ("type_tax_use", "=", "sale"),
                ("amount_type", "=", "percent"),
            ],
            limit=1,
        )
        unece_code_list_id = cls.env["unece.code.list"].create(
            {"type": "tax_categ", "name": "test", "code": "test"}
        )
        cls.invoice_tax.unece_categ_id = unece_code_list_id
        cls.invoice_tax.unece_type_id = unece_code_list_id
        cls.nsmap, cls.ns = cls.env["base.ubl"]._ubl_get_nsmap_namespace("Invoice-2")
        cls.xml_root = etree.Element("Invoice", nsmap=cls.nsmap)
        cls.invoice = cls.create_test_invoice(cls)
        cls.invoice.partner_id.vat = "BE000000000"
        cls.invoice.partner_id.street2 = "Test Street 2"
        cls.invoice.partner_id.parent_id = cls.invoice.company_id.partner_id

    def test_pdf_generate(self):
        content, doc_type = (
            self.env.ref("account.account_invoices")
            .with_context(no_embedded_ubl_xml=True, force_report_rendering=True)
            .env.ref("account.account_invoices")
            ._render_qweb_pdf(self.invoice.ids)
        )
        self.assertTrue(content)
        self.assertEqual(doc_type, "pdf")

    def test_ubl_generate(self):
        self.env["base.ubl"]._ubl_add_supplier_party(
            False,
            self.invoice.company_id,
            "AccountingSupplierParty",
            self.xml_root,
            self.ns,
        )
        with self.assertRaisesRegex(AssertionError, ".*partner is wrong.*"):
            self.env["base.ubl"]._ubl_add_supplier_party(
                self.invoice.partner_id,
                self.invoice.company_id,
                "AccountingSupplierParty",
                self.xml_root,
                self.ns,
            )
        self.env["base.ubl"]._ubl_add_customer_party(
            False,
            self.invoice.company_id,
            "AccountingCustomerParty",
            self.xml_root,
            self.ns,
        )
        self.env["base.ubl"]._ubl_add_customer_party(
            self.invoice.partner_id,
            False,
            "AccountingCustomerParty",
            self.xml_root,
            self.ns,
        )
        with self.assertRaisesRegex(AssertionError, ".*partner is wrong.*"):
            self.env["base.ubl"]._ubl_add_customer_party(
                self.invoice.partner_id,
                self.invoice.company_id,
                "AccountingCustomerParty",
                self.xml_root,
                self.ns,
            )
        self.invoice.partner_id.commercial_partner_id = (
            self.invoice.company_id.partner_id
        )
        self.env["base.ubl"]._ubl_add_customer_party(
            self.invoice.partner_id,
            self.invoice.company_id,
            "AccountingCustomerParty",
            self.xml_root,
            self.ns,
        )

    def test_ubl_generate_without_partner(self):
        # Should fail if company or partner fields is not provided.
        with self.assertRaisesRegex(UserError, ".*Missing.*"):
            self.env["base.ubl"]._ubl_add_supplier_party(
                False, False, "AccountingSupplierParty", self.xml_root, self.ns
            )

    def test_ubl_add_party(self):
        self.env["base.ubl"]._ubl_add_party(
            self.invoice.partner_id,
            False,
            "AccountingCustomerParty",
            self.xml_root,
            self.ns,
        )

    def test_ubl_add_language(self):
        self.env["base.ubl"]._ubl_add_language(
            self.invoice.partner_id.lang, self.xml_root, self.ns
        )

    def test_ubl_add_tax_scheme(self):
        tax_scheme_dict = self.env["base.ubl"]._ubl_get_tax_scheme_dict_from_partner(
            self.invoice.partner_id
        )
        tax_category = etree.SubElement(self.xml_root, self.ns["cac"] + "TaxCategory")
        self.env["base.ubl"]._ubl_add_tax_scheme(tax_scheme_dict, tax_category, self.ns)

    def test_get_xml_files_from_pdf(self):
        content, doc_type = (
            self.env.ref("account.account_invoices")
            .with_context(no_embedded_ubl_xml=True, force_report_rendering=True)
            .env.ref("account.account_invoices")
            ._render_qweb_pdf(self.invoice.ids)
        )
        self.env["base.ubl"].get_xml_files_from_pdf(content)

    def test_embed_xml_in_pdf(self):
        """
        Checking two methods:
            _ubl_check_xml_schema
            embed_xml_in_pdf
        """
        content, doc_type = (
            self.env.ref("account.account_invoices")
            .with_context(no_embedded_ubl_xml=True, force_report_rendering=True)
            .env.ref("account.account_invoices")
            ._render_qweb_pdf(self.invoice.ids)
        )
        fd = BytesIO(content)
        pdf = PdfFileReader(fd)
        pdf_root = pdf.trailer["/Root"]
        embeddedfiles = pdf_root["/Names"]["/EmbeddedFiles"]["/Names"]
        i = 0
        xmlfiles = {}  # key = filename, value = PDF obj
        for embeddedfile in embeddedfiles[:-1]:
            mime_res = mimetypes.guess_type(embeddedfile)
            if mime_res and mime_res[0] in ["application/xml", "text/xml"]:
                xmlfiles[embeddedfile] = embeddedfiles[i + 1]
            i += 1
        for _filename, xml_file_dict_obj in xmlfiles.items():
            xml_file_dict = xml_file_dict_obj.getObject()
            xml_string = xml_file_dict["/EF"]["/F"].getData()

            self.env["base.ubl"].new().embed_xml_in_pdf(
                xml_string, "factur-x.xml", pdf_content=content
            )
            xsd_file = "base_ubl/data/xsd-{}/common/UBL-{}-{}.xsd".format(
                "2.1", "CommonAggregateComponents", "2.1"
            )
            xsd_etree_obj = etree.parse(file_open(xsd_file))

            self.env["base.ubl"].new().ubl_parse_address(xsd_etree_obj, self.ns)
            self.env["base.ubl"].new().ubl_parse_delivery_details(
                xsd_etree_obj, self.ns
            )
            self.env["base.ubl"].new().ubl_parse_incoterm(xsd_etree_obj, self.ns)
            self.env["base.ubl"].new().ubl_parse_product(xsd_etree_obj, self.ns)

            self.env["base.ubl"].new().ubl_parse_party(xsd_etree_obj, self.ns)

            with self.assertRaisesRegex(IndexError, ".*out of range.*"):
                self.env["base.ubl"].new().ubl_parse_customer_party(
                    xsd_etree_obj, self.ns
                )
            with self.assertRaisesRegex(IndexError, ".*out of range.*"):
                self.env["base.ubl"].new().ubl_parse_supplier_party(
                    xsd_etree_obj, self.ns
                )

            with self.assertRaisesRegex(
                UserError, ".*The UBL XML file is not valid against the official.*"
            ):
                self.env["base.ubl"].new()._ubl_check_xml_schema(
                    xml_string, "Statement"
                )

    def test_ubl_add_line_item(self):
        product = self.env.ref("product.product_product_4")
        self.env["base.ubl"]._ubl_add_line_item(
            1,
            "test",
            product,
            "purchase",
            2,
            product.uom_id,
            self.xml_root,
            self.ns,
            currency=self.currency_data["currency"],
            price_subtotal=100,
        )
        product.uom_id.unece_code = False
        with self.assertRaisesRegex(UserError, ".*Missing UNECE.*"):
            self.env["base.ubl"]._ubl_add_line_item(
                1,
                "test",
                product,
                "purchase",
                2,
                product.uom_id,
                self.xml_root,
                self.ns,
                currency=self.currency_data["currency"],
                price_subtotal=100,
            )

    def test_ubl_add_tax_subtotal(self):
        self.env["base.ubl"]._ubl_add_tax_subtotal(
            100,
            100,
            self.invoice_tax,
            self.currency_data["currency"].name,
            self.xml_root,
            self.ns,
        )

    def test_ubl_get_version(self):
        with self.assertRaisesRegex(UserError, ".*The UBL XML file does not contain.*"):
            self.env["base.ubl"]._ubl_get_version(self.xml_root, "Invoice", self.ns)

    def test_ubl_add_party_tax_scheme(self):
        self.env["base.ubl"]._ubl_add_party_tax_scheme(
            self.invoice.partner_id, self.xml_root, self.ns
        )

    def test_ubl_add_delivery(self):
        self.env["base.ubl"]._ubl_add_delivery(
            self.invoice.partner_id, self.xml_root, self.ns
        )

    def test_ubl_add_delivery_terms(self):
        self.env["base.ubl"]._ubl_add_delivery_terms(
            self.invoice.invoice_incoterm_id, self.xml_root, self.ns
        )

    def test_ubl_add_payment_terms(self):
        self.env["base.ubl"]._ubl_add_payment_terms(
            self.invoice.invoice_payment_term_id, self.xml_root, self.ns
        )

    def create_test_invoice(
        self, product=False, qty=1, price=12.42, discount=0, validate=True
    ):
        aio = self.env["account.move"]
        aao = self.env["account.account"]
        company = self.company_data["company"]
        account_revenue = aao.search(
            [("code", "=", "707100"), ("company_id", "=", company.id)], limit=1
        )
        if not account_revenue:
            account_revenue = aao.with_user(self.internal_user).create(
                {
                    "code": "707100",
                    "name": "Product Sales - (test)",
                    "company_id": company.id,
                    "user_type_id": self.env.ref(
                        "account.data_account_type_revenue"
                    ).id,
                }
            )
        # validate invoice
        if not product:
            product = self.env.ref("product.product_product_4")
        incoterm_id = self.env["account.incoterms"].search(
            [("code", "!=", False)], limit=1
        )
        product.barcode = "1234567890"
        invoice = aio.with_user(self.internal_user).create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "currency_id": self.currency_data["currency"].id,
                "move_type": "out_invoice",
                "company_id": company.id,
                "name": "SO1242",
                "invoice_incoterm_id": incoterm_id.id or False,
                "invoice_payment_term_id": self.env.ref(
                    "account.account_payment_term_end_following_month"
                ).id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "quantity": qty,
                            "price_unit": price,
                            "discount": discount,
                            "name": product.name,
                            "account_id": account_revenue.id,
                            "tax_ids": [(6, 0, [self.invoice_tax.id])],
                        },
                    )
                ],
            }
        )
        if validate:
            invoice.action_post()
        return invoice
