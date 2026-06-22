# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from lxml import etree

from odoo import fields
from odoo.fields import Command
from odoo.tests.common import HttpCase


class PurchaseOrderUblMixin:
    """Minimal common setup to build a PO that can be UBL-serialized."""

    @classmethod
    def _setup_purchase_ubl_records(cls):
        cls.vat_tax_type = cls.env.ref("account_tax_unece.tax_type_vat")
        cls.s_tax_categ = cls.env.ref("account_tax_unece.tax_categ_s")
        cls.country = cls.env.company.country_id
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "ACME Vendor",
                "country_id": cls.country.id,
                "street": "Foo street 1",
                "city": "Lausanne",
                "zip": "1000",
            }
        )
        cls.tax_18 = cls.env["account.tax"].create(
            {
                "name": "VAT purchase 18.0%",
                "description": "VAT-buy-18.0",
                "type_tax_use": "purchase",
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": cls.vat_tax_type.id,
                "unece_categ_id": cls.s_tax_categ.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "default_code": "TEST-001",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "purchase_ok": True,
                "list_price": 10.0,
                "standard_price": 5.0,
                "supplier_taxes_id": [Command.set(cls.tax_18.ids)],
            }
        )
        cls.order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "date_planned": fields.Datetime.now(),
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_qty": 3,
                            "price_unit": 12.0,
                            "name": cls.product.display_name,
                            "date_planned": fields.Datetime.now(),
                            "taxes_id": [Command.set(cls.tax_18.ids)],
                        }
                    )
                ],
            }
        )
        return cls.order

    def _parse_ubl_xml(self, xml_string):
        xml_bytes = xml_string.encode() if isinstance(xml_string, str) else xml_string
        return xml_bytes, etree.fromstring(xml_bytes)

    def _assert_valid_ubl_xml(self, xml_string, document, version):
        """Parse ``xml_string``, check the root tag and validate against XSD."""
        self.assertTrue(xml_string, "Generated UBL XML is empty")
        xml_bytes, parsed = self._parse_ubl_xml(xml_string)
        self.assertEqual(etree.QName(parsed.tag).localname, document)
        # XSD validation via base.ubl (raises UserError if invalid)
        self.order._ubl_check_xml_schema(xml_bytes, document, version=version)
        return parsed

    @staticmethod
    def _classified_tax_categories(xml_root):
        """Return all ``ClassifiedTaxCategory`` nodes found under ``Item``."""
        return xml_root.findall(".//{*}Item/{*}ClassifiedTaxCategory")


class PurchaseOrderUblCommon(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_hour = cls.env.ref("uom.product_uom_hour")
        cls.vat_tax_type = cls.env.ref("account_tax_unece.tax_type_vat")
        cls.s_tax_categ = cls.env.ref("account_tax_unece.tax_categ_s")
        cls.country = cls.env.company.country_id
        cls.vendors = cls.env["res.partner"].create(
            [
                {"name": "Azure Interior", "country_id": cls.country.id},
                {"name": "Gemini Furniture", "country_id": cls.country.id},
                {"name": "Deco Addict", "country_id": cls.country.id},
                {"name": "Wood Corner", "country_id": cls.country.id},
            ]
        )
        cls.tax_18 = cls.env["account.tax"].create(
            {
                "name": "VAT purchase 18.0%",
                "description": "VAT-buy-18.0",
                "type_tax_use": "purchase",
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": cls.vat_tax_type.id,
                "unece_categ_id": cls.s_tax_categ.id,
            }
        )
        cls.products = {
            name: cls._create_product(name, uom)
            for name, uom in {
                "Delivery Grid": cls.uom_unit,
                "Delivery Pallet": cls.uom_unit,
                "Conference Room": cls.uom_unit,
                "Consulting": cls.uom_hour,
                "Flipover": cls.uom_unit,
                "Office Lamp": cls.uom_unit,
                "Large Desk": cls.uom_unit,
                "Office Chair": cls.uom_unit,
                "Drawer": cls.uom_unit,
                "Acoustic Bloc Screens": cls.uom_unit,
            }.items()
        }

        cls.purchase_orders = cls._create_purchase_orders()

    @classmethod
    def _create_product(cls, name, uom):
        return cls.env["product.product"].create(
            {
                "name": name,
                "uom_id": uom.id,
                "purchase_ok": True,
                "supplier_taxes_id": [Command.set(cls.tax_18.ids)],
            }
        )

    @classmethod
    def _create_purchase_order_lines(cls, product_name, price, quantity, delay=0):
        product = cls.products[product_name]
        return Command.create(
            {
                "product_id": product.id,
                "price_unit": price,
                "product_qty": quantity,
                "product_uom": product.uom_id.id,
                "date_planned": fields.Datetime.now() + timedelta(days=delay),
                "taxes_id": [Command.set(cls.tax_18.ids)],
            },
        )

    @classmethod
    def _create_purchase_order(cls, vendor, lines, state="draft"):
        purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": vendor.id,
                "user_id": cls.env.ref("base.user_admin").id,
                "order_line": [
                    cls._create_purchase_order_lines(**line) for line in lines
                ],
            }
        )
        if state != "draft":
            purchase_order.write({"state": state})
        return purchase_order

    @classmethod
    def _create_purchase_orders(cls):
        return [
            cls._create_purchase_order(
                cls.vendors[0],
                [
                    {"product_name": "Delivery Grid", "price": 100.0, "quantity": 1},
                    {"product_name": "Delivery Pallet", "price": 50.0, "quantity": 2},
                ],
            ),
            cls._create_purchase_order(
                cls.vendors[1],
                [
                    {"product_name": "Conference Room", "price": 200.0, "quantity": 1},
                    {
                        "product_name": "Consulting",
                        "price": 100.0,
                        "quantity": 10,
                        "delay": 7,
                    },
                ],
            ),
            cls._create_purchase_order(
                cls.vendors[2],
                [
                    {"product_name": "Flipover", "price": 20.0, "quantity": 3},
                    {"product_name": "Office Lamp", "price": 15.0, "quantity": 4},
                    {"product_name": "Large Desk", "price": 150.0, "quantity": 1},
                ],
            ),
            cls._create_purchase_order(
                cls.vendors[3],
                [
                    {
                        "product_name": "Delivery Pallet",
                        "price": 85.50,
                        "quantity": 6,
                        "delay": 5,
                    },
                    {
                        "product_name": "Flipover",
                        "price": 1690.0,
                        "quantity": 5,
                        "delay": 5,
                    },
                    {
                        "product_name": "Large Desk",
                        "price": 800.0,
                        "quantity": 7,
                        "delay": 5,
                    },
                ],
                state="sent",
            ),
            cls._create_purchase_order(
                cls.vendors[1],
                [
                    {"product_name": "Office Chair", "price": 2010.0, "quantity": 3},
                    {"product_name": "Drawer", "price": 876.0, "quantity": 3},
                ],
            ),
            cls._create_purchase_order(
                cls.vendors[0],
                [
                    {"product_name": "Delivery Pallet", "price": 58.0, "quantity": 9},
                    {"product_name": "Delivery Grid", "price": 65.0, "quantity": 3},
                    {
                        "product_name": "Acoustic Bloc Screens",
                        "price": 154.5,
                        "quantity": 4,
                    },
                ],
            ),
            cls._create_purchase_order(
                cls.vendors[3],
                [
                    {"product_name": "Office Chair", "price": 130.5, "quantity": 5},
                    {"product_name": "Delivery Pallet", "price": 38.0, "quantity": 15},
                ],
                state="purchase",
            ),
        ]
