# Copyright 2019 Onestein (<https://www.onestein.eu>)
# © 2017-2020 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from lxml import etree

from odoo.tests.common import TransactionCase

from .common import DummyRecord


class TestBaseUblGenerate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_ubl = cls.env["base.ubl"]
        cls.company = DummyRecord(
            name="Test Company",
            partner_id=DummyRecord(
                name="Test Company Partner",
                country_id=DummyRecord(code="DE"),
                commercial_partner_id=DummyRecord(
                    name="Test Company Commercial",
                    ref="TC1234",
                    country_id=DummyRecord(code="DE"),
                ),
            ),
        )
        cls.partner = DummyRecord(
            name="Test Partner",
            company_id=cls.company,
            country_id=DummyRecord(code="CH"),
            commercial_partner_id=DummyRecord(
                name="Test Partner Commercial", ref="TP1234"
            ),
        )
        cls.product = DummyRecord(
            name="Test Product",
            uom_id=DummyRecord(id=1, name="Unit"),
        )
        cls.account = DummyRecord(
            code="707100",
            name="Product Sales - (test)",
            company_id=cls.company,
            account_type="income",
        )
        cls.tax = DummyRecord(
            name="German VAT purchase 18.0%",
            unece_type_id=True,
            unece_categ_id=True,
            amount_type="percent",
            amount=18,
            type_tax_use="sale",
            company_id=cls.company,
        )
        cls.invoice_line = DummyRecord(
            product_id=cls.product,
            product_uom_id=cls.product.uom_id,
            quantity=1,
            price_unit=12.42,
            discount=0,
            name=cls.product.name,
            account_id=cls.account,
            tax_ids=[cls.tax],
        )
        cls.invoice = DummyRecord(
            partner_id=cls.partner,
            company_id=cls.company,
            currency_id=DummyRecord(name="EUR"),
            move_type="out_invoice",
            name="SO1242",
            invoice_line_ids=[cls.invoice_line],
        )

    def test_ubl_generate(self):
        nsmap, ns = self.base_ubl._ubl_get_nsmap_namespace("Invoice-2")
        xml_root = etree.Element("Invoice", nsmap=nsmap)
        self.base_ubl._ubl_add_supplier_party(
            None, self.invoice.company_id, "AccountingSupplierParty", xml_root, ns
        )
        self.base_ubl._ubl_add_customer_party(
            self.invoice.partner_id, None, "AccountingCustomerParty", xml_root, ns
        )
        # Check that the tags were added
        supplier = xml_root.find(ns["cac"] + "AccountingSupplierParty")
        customer = xml_root.find(ns["cac"] + "AccountingCustomerParty")
        self.assertIsNotNone(supplier)
        self.assertIsNotNone(customer)
