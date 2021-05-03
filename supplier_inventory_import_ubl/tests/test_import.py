# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.exceptions import Warning as UserError

# product.product_product_35 is CD
# product.product_product_23 is processor AMD
# product.product_product_11 is iPod


class TestImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestImport, cls).setUpClass()

    def test_only_one_default_code(self):
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient(
            "only_one_default_code"
        )
        res = wizard.process_document()
        ref = self.env.ref
        info = ref("product.product_product_23").supplier_stock_info
        self.assertEqual(info and info[:4], "Wood")
        info = ref("product.product_product_11").supplier_stock_info
        self.assertEqual(info, False)
        self.assertEqual(
            res.get("res_model"),
            "product.product",
            "Current model should be product.product",
        )

    def test_no_seller_reference(self):
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient(
            "no_seller_reference"
        )
        res = wizard.process_document()
        info = self.env.ref("product.product_product_35").supplier_stock_info
        self.assertEqual(info and info[:4], "Wood")
        self.assertEqual(
            res.get("res_model"),
            "product.product",
            "Current model should be product.product",
        )

    def test_unknow_supplier(self):
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient(
            "unknow_supplier"
        )
        with self.assertRaises(UserError):
            wizard.process_document()

    def test_same_product(self):
        """ The product has 2 inventory lines according its lot """
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient(
            "same_product"
        )
        wizard.process_document()
        prd = self.env.ref("product.product_product_23")
        self.assertEqual(
            prd.supplier_stock_info and prd.supplier_stock_info[:4], "Wood"
        )
        self.assertEqual(
            prd.supplier_stock, 17, "Stock should be the sum of the 2 inventory lines"
        )

    def test_same_barcode(self):
        """ The product has 2 inventory lines according its lot """
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient(
            "same_barcode"
        )
        wizard.process_document()
        prd = self.env.ref("supplier_inventory_import_ubl.shoes_with_barcode")
        self.assertEqual(
            prd.supplier_stock_info and prd.supplier_stock_info[:4], "Wood"
        )
        self.assertEqual(
            prd.supplier_stock, 17, "Stock should be the sum of the 2 inventory lines"
        )

    def test_main(self):
        self.env["inventory.ubl.helper"]._import_main_xml_file_when_demo_and_test()
        supplier = self.env.ref("supplier_inventory_import_ubl.res_partner_1")
        ref = self.env.ref
        # A message have been sent on the supplier record
        last_message = sorted(supplier.message_ids, reverse=True)[0]
        self.assertEqual(
            last_message.body,
            u"<p>These product codes ['??', 'UN'] have no matching code in ERP</p>",
        )
        info = ref("product.product_product_35").supplier_stock_info
        self.assertEqual(info and info[:4], "Wood")
        info = ref(
            "supplier_inventory_import_ubl.product_product_9"
        ).supplier_stock_info
        self.assertEqual(info and info[:4], "Wood")
        # Below must be false because iPod has 2 variants and matched
        # with only one supplier code field found in supplierinfo
        # one supplier code can't set stock to 2 products
        # This problem is not found in upper versions like v10 that have
        # product_id field in supplierinfo
        self.assertEqual(ref("product.product_product_11").supplier_stock_info, False)
        # checks on supplierinfo
        self.assertNotEqual(
            ref("supplier_inventory_import_ubl.supp_inf_wood_cd").stock, 0.0
        )
        self.assertNotEqual(
            ref("supplier_inventory_import_ubl.supp_inf_wood_cd2").stock, 0.0
        )
        self.assertNotEqual(
            ref("supplier_inventory_import_ubl.supp_inf_wood_bin").stock, 0.0
        )
