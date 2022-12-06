# Copyright 2022 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger

from .common import get_test_data


class TestUblOrderImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.supplier = cls.env["res.partner"].create({"name": "Medical"})

    def _all_products(self):
        return (
            self.env["product.product"]
            .with_context(active_test=False)
            .search([], order="id")
        )

    @mute_logger("odoo.addons.product_import.wizard.product_import")
    def test_ubl_catalogue_import(self):
        tests = get_test_data(self.env)
        for filename, expected in tests.items():
            xml_file_b64 = expected._as_base64()
            products_before = self._all_products()
            wiz = self.env["product.import"].create(
                {
                    "product_file": xml_file_b64,
                    "product_filename": filename,
                }
            )
            wiz.import_button()
            new_products = self._all_products() - products_before
            self.assertEqual(len(new_products), len(expected["products"]))
            for product, p_expect in zip(new_products, expected["products"]):
                self.assertEqual(product.active, p_expect["active"])
                self.assertEqual(product.name, p_expect["name"])
                self.assertEqual(product.default_code, p_expect["code"])
                self.assertEqual(product.barcode, p_expect["barcode"])
                self.assertEqual(product.description, p_expect["description"])
                self.assertEqual(product.uom_id, p_expect["uom"])
                if p_expect["company"]:
                    self.assertEqual(product.company_id, p_expect["company"])
                else:
                    self.assertFalse(product.company_id)
                # Supplier info
                [supplierinfo] = product.seller_ids
                self.assertEqual(supplierinfo.name, self.supplier)
                self.assertEqual(supplierinfo.product_code, p_expect["product_code"])
                self.assertEqual(supplierinfo.min_qty, p_expect["min_qty"])
                self.assertEqual(supplierinfo.price, p_expect["price"])
                self.assertEqual(supplierinfo.currency_id, p_expect["currency"])
                self.assertEqual(
                    supplierinfo.date_start, supplierinfo.create_date.date()
                )
                self.assertEqual(supplierinfo.date_end, False)
                self.assertEqual(
                    supplierinfo.company_id, p_expect["company"] or self.env.company
                )
