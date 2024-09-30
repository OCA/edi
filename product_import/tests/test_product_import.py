# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import TestCommon

PARSED_CATALOG = {
    "date": "2016-08-01",
    "doc_type": "catalogue",
    "products": [
        {
            "barcode": "1234567890924",
            "code": "998000924",
            "currency": {"iso": "EUR"},
            "description": False,
            "external_ref": "101",
            "min_qty": 1.0,
            "name": "Vlies-Haube Romed Clip blau",
            "price": 1.35,
            "product_code": "998000924",
            "uom": {"unece_code": False},
        },
        {
            "barcode": "1234567890114",
            "code": "MNTR011",
            "currency": {"iso": "EUR"},
            "description": "Photo copy paper 80g A4, package of 500 sheets.",
            "external_ref": "102",
            "min_qty": 1.0,
            "name": "Copy paper",
            "price": 12.55,
            "product_code": "MNTR011",
            "uom": {"unece_code": False},
        },
        {
            # Archived product
            "barcode": "1234567890124",
            "code": "MNTR012",
            "currency": {"iso": "EUR"},
            "description": "Photo copy paper 80g A4, carton of 10 units "
            "with 500 sheets each",
            "external_ref": "103",
            "min_qty": 20.0,
            "name": "Copy paper",
            "price": 91.5,
            "product_code": "MNTR012",
            "uom": {"unece_code": "C62"},
            "active": False,
        },
    ],
    "ref": "1387",
    "company": {"name": "Customer ABC"},
    "seller": {
        "contact": False,
        "email": False,
        "id_number": [],
        "name": "Catalogue Vendor",
        "phone": False,
        "vat": False,
        "website": False,
    },
}


class TestProductImport(TestCommon):
    """Test product create/update."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parsed_catalog = dict(PARSED_CATALOG)
        cls.parsed_catalog["chatter_msg"] = []

    def test_get_seller(self):
        # Not found
        with self.assertRaises(UserError):
            seller = self.wiz_model._get_seller(self.parsed_catalog)
        # Found
        seller = self.wiz_model.with_company(self.company.id)._get_seller(
            self.parsed_catalog
        )
        self.assertEqual(seller, self.supplier)

    def test_get_company_id(self):
        # Test found company_id
        company_id = self.wiz_model._get_company_id(self.parsed_catalog)
        self.assertEqual(company_id, self.company.id)
        # Test not found company_id
        new_catalog = dict(self.parsed_catalog)
        del new_catalog["company"]
        company_id = self.wiz_model._get_company_id(new_catalog)
        self.assertIs(company_id, False)

    def test_product_import(self):
        # product.product
        products = self.wiz_model._create_products(
            self.parsed_catalog, seller=self.supplier
        )
        self.assertEqual(len(products), 3)
        for product, parsed in zip(products, PARSED_CATALOG["products"]):

            # Expected
            expected = {
                "code": parsed["code"],
                "seller": PARSED_CATALOG["seller"]["name"],
                "min_qty": parsed["min_qty"],
                "price": parsed["price"],
                "currency": parsed["currency"]["iso"],
                "type": "product",
                "uom_id": 1,  # Units
                "uom_po_id": 1,
                "active": parsed.get("active", True),
            }

            # product.product "Product Variant"
            [p_supplierinfo] = product.seller_ids
            p_values = {
                "code": product.default_code,
                "seller": p_supplierinfo.name.name,
                "min_qty": p_supplierinfo.min_qty,
                "price": p_supplierinfo.price,
                "currency": p_supplierinfo.currency_id.name,
                "type": product.type,
                "uom_id": product.uom_id.id,
                "uom_po_id": product.uom_po_id.id,
                "active": product.active,
            }
            for key in "name", "barcode", "description":
                expected[key] = parsed[key]
                p_values[key] = getattr(product, key)

            # product.template "Product"
            product_tmpl = product.product_tmpl_id
            pt_values = {
                **p_values,
                "code": product_tmpl.default_code,
                "uom_id": product_tmpl.uom_id.id,
                "uom_po_id": product_tmpl.uom_po_id.id,
            }
            for key in "name", "barcode", "description", "type", "active":
                pt_values[key] = getattr(product_tmpl, key)

            self.assertEqual(p_values, expected)
            self.assertEqual(pt_values, expected)
            self.assertEqual(product.seller_ids, product_tmpl.seller_ids)

    def test_import_button(self):
        form = self.wiz_form
        with self._mock("_parse_file") as mocked:
            mocked.return_value = self.parsed_catalog
            form.product_filename = "test.xml"
            mocked.assert_not_called()
            form.product_file = "AA=="
            mocked.assert_called()
            mocked.reset_mock()

            wiz = form.save()
            mocked.assert_not_called()
            wiz.import_button()
            mocked.assert_called()
