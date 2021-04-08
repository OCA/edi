# Copyright 2019 Onestein (<https://www.onestein.eu>)
# © 2017-2020 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests.common import HttpCase


class TestUblInvoice(HttpCase):
    def test_pdf_generate(self):
        invoice = self.create_test_invoice()
        content, doc_type = (
            self.env.ref("account.account_invoices")
            .with_context(no_embedded_ubl_xml=True, force_report_rendering=True)
            .env.ref("account.account_invoices")
            ._render_qweb_pdf(invoice.ids)
        )
        self.assertTrue(content)
        self.assertEqual(doc_type, "pdf")

    def test_ubl_generate(self):
        invoice = self.create_test_invoice()
        nsmap, ns = self.env["base.ubl"]._ubl_get_nsmap_namespace("Invoice-2")
        xml_root = etree.Element("Invoice", nsmap=nsmap)

        self.env["base.ubl"]._ubl_add_supplier_party(
            False, invoice.company_id, "AccountingSupplierParty", xml_root, ns
        )
        self.env["base.ubl"]._ubl_add_customer_party(
            invoice.partner_id, False, "AccountingCustomerParty", xml_root, ns
        )

    def create_test_invoice(
        self, product=False, qty=1, price=12.42, discount=0, validate=True
    ):
        aio = self.env["account.move"]
        aao = self.env["account.account"]
        ato = self.env["account.tax"]
        company = self.env.ref("base.main_company")
        account_revenue = aao.search(
            [("code", "=", "707100"), ("company_id", "=", company.id)], limit=1
        )
        if not account_revenue:
            account_revenue = aao.create(
                {
                    "code": "707100",
                    "name": "Product Sales - (test)",
                    "company_id": company.id,
                    "user_type_id": self.env.ref(
                        "account.data_account_type_revenue"
                    ).id,
                }
            )
        taxes = ato.search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "sale"),
                ("unece_type_id", "!=", False),
                ("unece_categ_id", "!=", False),
                ("amount_type", "=", "percent"),
            ]
        )
        if taxes:
            tax = taxes[0]
        else:
            unece_type_id = self.env.ref("account_tax_unece.tax_type_vat").id
            unece_categ_id = self.env.ref("account_tax_unece.tax_categ_s").id
            tax = ato.create(
                {
                    "name": u"German VAT purchase 18.0%",
                    "description": "DE-VAT-sale-18.0",
                    "company_id": company.id,
                    "type_tax_use": "sale",
                    "price_include": False,
                    "amount": 18,
                    "amount_type": "percent",
                    "unece_type_id": unece_type_id,
                    "unece_categ_id": unece_categ_id,
                }
            )
        # validate invoice
        if not product:
            product = self.env.ref("product.product_product_4")
        invoice = aio.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "currency_id": self.env.ref("base.EUR").id,
                "move_type": "out_invoice",
                "company_id": company.id,
                "name": "SO1242",
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
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )
        if validate:
            invoice.action_post()
        return invoice
