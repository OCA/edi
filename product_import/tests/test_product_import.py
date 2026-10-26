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
            "min_qty": 5.0,
            "name": "Copy paper",
            "price": 12.55,
            "product_code": "MNTR011",
            "uom": {"unece_code": False},
            "sale_delay": 3,
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
            "sale_delay": 1,
        },
    ],
    "ref": "1387",
    "company": {"name": "Customer ABC"},
    "seller": {"name": "Catalogue Vendor"},
}
PARSED_CATALOG2 = {
    "date": "2016-09-03",
    "doc_type": "catalogue",
    "products": [
        {
            "barcode": "1234567890114",
            "code": "MNTR011",
            "active": False,
            "name": "Konnektor 1/4x1/4 CB4629",
            "description": "Konnektor 1/4x1/4 CB4629",
            "external_ref": "201459",
            "uom": {"unece_code": "H87"},
            "product_code": "201459",
            "weight": 29.0,
            "weight_uom": False,
            "price": 0.0,
            "currency": {"iso": "EUR"},
            "min_qty": 9.0,
            "manufacturer_ref": False,
            "sale_delay": 11,
        },
    ],
    "ref": "214R",
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
        product_obj = self.env["product.product"].with_context(active_test=False)
        existing = product_obj.search([], order="id")

        wiz = self.wiz_model.create(
            {"product_file": b"====", "product_filename": "test_import.xml"}
        )
        with self._mock("parse_product_catalogue", return_value=self.parsed_catalog):
            wiz.import_button()
        products = product_obj.search([], order="id") - existing
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
            self.assertEqual(
                product.seller_ids.mapped("delay")[0], parsed.get("sale_delay", 0)
            )
            # Pricelist is linked to the Product Template, not the Product Variant
            self.assertEqual(
                product.seller_ids.product_tmpl_id, product.product_tmpl_id
            )
            self.assertFalse(product.seller_ids.product_id)

    def test_product_import_change(self):
        # product.product
        product_obj = self.env["product.product"].with_context(active_test=False)
        existing = product_obj.search([], order="id")
        parsed_catalog2 = {**PARSED_CATALOG2, "chatter_msg": []}

        wiz = self.wiz_model.create(
            {"product_file": b"====", "product_filename": "test_import.xml"}
        )

        # 1st import
        with self._mock("parse_product_catalogue", return_value=self.parsed_catalog):
            wiz.import_button()

        # 2nd import
        with self._mock("parse_product_catalogue", return_value=parsed_catalog2):
            wiz.import_button()
        products = product_obj.search([], order="id") - existing
        self.assertEqual(len(products), 3)
        for product, parsed in zip(products, PARSED_CATALOG["products"]):
            if product.default_code == "MNTR011":
                [parsed] = PARSED_CATALOG2["products"]

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
            [p_supplierinfo] = product.seller_ids[:1]
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
            self.assertEqual(
                product.seller_ids.mapped("delay")[0], parsed.get("sale_delay", 0)
            )

        # 3rd import
        with self._mock("parse_product_catalogue", return_value=self.parsed_catalog):
            wiz.import_button()

        self.assertEqual(product_obj.search([], order="id") - existing, products)
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
            self.assertEqual(
                product.seller_ids.mapped("delay")[0], parsed.get("sale_delay", 0)
            )
            # Pricelist is linked to the Product Template, not the Product Variant
            self.assertEqual(
                product.seller_ids.product_tmpl_id, product.product_tmpl_id
            )
            self.assertFalse(product.seller_ids.product_id)

    def test_prepare_values(self):
        # Check that only changed values are written to the existing product

        # product.product
        product_obj = self.env["product.product"].with_context(active_test=False)
        existing = product_obj.search([], order="id")
        parsed_catalog2 = {**PARSED_CATALOG2, "chatter_msg": []}

        wiz = self.wiz_model.create(
            {"product_file": b"====", "product_filename": "test_import.xml"}
        )

        # Initial import
        with self._mock("parse_product_catalogue", return_value=self.parsed_catalog):
            wiz.import_button()

        # 2nd import - 1 product changed
        catalogue = parsed_catalog2
        company_id = wiz._get_company_id(catalogue)
        seller = wiz.with_company(company_id)._get_seller(catalogue)
        chatter_msg = catalogue["chatter_msg"]
        [parsed_product] = catalogue["products"]
        product_vals = wiz._prepare_product(
            parsed_product,
            seller=seller,
            company_id=company_id,
            chatter_msg=chatter_msg,
        )
        product = product_obj.search([("default_code", "=", "MNTR011")])
        seller_data = product_vals["seller_ids"][0][2]
        expected = {
            "active": False,
            "name": parsed_product["name"],
            "description": parsed_product["description"],
            "recordset": product,
            "seller_ids": [(1, product.seller_ids.id, seller_data)],
        }
        self.assertEqual(product_vals, expected)

        # Save
        saved = wiz._save_product(product_vals, chatter_msg=chatter_msg)
        self.assertEqual(saved, product)

        # 3rd import - reimport initial catalogue - still only 1 product changed
        catalogue = self.parsed_catalog
        prepared_vals = []
        for parsed_product in catalogue["products"]:
            vals = wiz._prepare_product(
                parsed_product,
                seller=seller,
                company_id=company_id,
                chatter_msg=chatter_msg,
            )
            prepared_vals.append(vals)

        seller_data = prepared_vals[1]["seller_ids"][0][2]
        parsed_product = catalogue["products"][1]
        expected = {
            "active": True,
            "name": parsed_product["name"],
            "description": parsed_product["description"],
            "recordset": product,
            "seller_ids": [(1, product.seller_ids.id, seller_data)],
        }
        self.assertEqual(prepared_vals, [{}, expected, {}])

        # Save
        saved = wiz._save_product(prepared_vals[1], chatter_msg=chatter_msg)
        self.assertEqual(saved, product)

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
