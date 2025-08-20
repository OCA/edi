# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import date, datetime
from unittest.mock import patch

from lxml import etree

from odoo.exceptions import UserError
from odoo.modules.module import get_module_path

from odoo.addons.base.tests.common import BaseCommon


class TestVoxelSaleOrderImportCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env["sale.order"]
        cls.AccountTax = cls.env["account.tax"]
        cls.ResPartner = cls.env["res.partner"]
        # This pricelist doesn't show the discount
        pricelist_test = cls.env["product.pricelist"].create(
            {"name": "pricelist test", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.customer_test = cls.ResPartner.create(
            {
                "name": "CUSTOMER TEST",
                "street": "Av Alcalde Pere Molas",
                "city": "Vila-seca",
                "zip": "43222",
                "ref": "F111",
                "email": "customertest@example.com",
                "state_id": cls.env.ref("base.state_es_t").id,
                "country_id": cls.env.ref("base.es").id,
                "property_product_pricelist": pricelist_test.id,
            }
        )
        cls.product_test_1 = cls.env["product.product"].create(
            {"default_code": "111111", "name": "PRODUCT TEST"}
        )
        cls.supplierinfo_product_test_1 = cls.env["product.customerinfo"].create(
            {
                "partner_id": cls.customer_test.id,
                "product_tmpl_id": cls.product_test_1.product_tmpl_id.id,
                "product_id": cls.product_test_1.id,
                "product_code": "SP11111",
                "product_name": "SUPPLIER PRODUCT TEST",
            }
        )
        cls.product_test_2 = cls.env["product.product"].create(
            {"default_code": "222222", "name": "PRODUCT TEST 2"}
        )
        # Hypothetical unit of measure to be able to load the test file
        # catching the voxel unit of measure called 'Cajas' for the
        # first order line
        cls.boxes_uom = cls.env["uom.uom"].create(
            {
                "name": "Boxes 3x3x3",
                "voxel_code": "Cajas",
                "category_id": cls.env.ref("uom.product_uom_unit").id,
                "uom_type": "bigger",
                "factor_inv": 9.0,
            }
        )

    def _create_document_from_test_file(self):
        # read file
        filename = "Pedido_20190619_145750_0611125750634.xml"
        module_path = get_module_path("edi_voxel_sale_order_import_oca")
        file_path = os.path.join(module_path, "tests/voxel_xml", filename)
        with open(file_path) as file:
            content = file.read()
        # call method
        return self.SaleOrder.create_document_from_xml(
            content, filename, self.env.company
        )


class TestVoxelSaleOrderImport(TestVoxelSaleOrderImportCommon):
    def test_create_document_from_xml(self):
        sale_order = self._create_document_from_test_file()
        # check the import was successful
        # check general data
        self.assertEqual(sale_order.client_order_ref, "1111")
        self.assertEqual(sale_order.currency_id.name, "EUR")
        self.assertEqual(sale_order.commitment_date, datetime(2019, 6, 19))
        self.assertEqual(sale_order.date_order, datetime(2019, 6, 19))
        self.assertEqual(sale_order.validity_date, date(2019, 6, 19))
        # check supplier, client and customer
        self.assertEqual(sale_order.partner_id, self.customer_test)
        self.assertEqual(sale_order.partner_shipping_id, self.customer_test)
        # check order line 1
        so_line = sale_order.order_line[0]
        self.assertEqual(so_line.product_id, self.product_test_1)
        self.assertEqual(so_line.product_uom, self.boxes_uom)
        self.assertEqual(so_line.product_uom_qty, 2)
        # check order line 2
        so_line = sale_order.order_line[1]
        self.assertEqual(so_line.product_id, self.product_test_2)
        self.assertEqual(so_line.product_uom, self.env.ref("uom.product_uom_unit"))
        self.assertEqual(so_line.product_uom_qty, 2)

    def test_parse_partner_data_voxel(self):
        data = {}
        with self.assertRaises(UserError):
            self.SaleOrder._parse_partner_data_voxel(data=data)

        data = {"ref": "F111"}
        result = self.SaleOrder._parse_partner_data_voxel(data=data)
        self.assertEqual(result, self.customer_test)

        data = {
            "ref": "F11112",
            "name": "CUSTOMER TEST",
            "city": "Vila-seca",
            "zip": "43222",
            "email": "customertest@example.com",
            "country_id": self.env.ref("base.es").code_alpha3,
            "state_id": self.env.ref("base.state_es_t").name,
        }
        result = self.SaleOrder._parse_partner_data_voxel(data=data)
        self.assertEqual(result, self.customer_test)

    def _mk_root(self, **params):
        root = etree.Element("Root")
        pairs = params.get("pairs", [])
        supplier = params.get("supplier", False)
        if not params.get("supplier", False):
            comments_el = etree.SubElement(root, "Comments")
            for subject, msg in pairs:
                attrs = {}
                if subject is not None:
                    attrs["Subject"] = subject
                if msg is not None:
                    attrs["Msg"] = msg
                etree.SubElement(comments_el, "Comment", **attrs)
        elif supplier:
            etree.SubElement(root, "Supplier", {"SupplierID": params["SupplierID"]})
        return root

    def _call(self, vals, root):
        errors = []
        self.SaleOrder._parse_comments_data_voxel(vals, root, errors)
        return vals, errors

    def test_parse_taxes_product_voxel(self):
        vals0 = {"keep": "me"}
        root = etree.Element("Root")
        vals, errors = self._call(dict(vals0), root)
        self.assertEqual(vals, vals0)
        self.assertEqual(errors, [])

        root = self._mk_root(**{"pairs": [("Subject 1", "Message 1")]})
        vals, _ = self._call({}, root)
        self.assertEqual(vals.get("note"), "Subject 1:\nMessage 1")

        root = self._mk_root(**{"pairs": [("Only Subject", None)]})
        vals, _ = self._call({}, root)
        self.assertEqual(vals.get("note"), "Only Subject")

        root = self._mk_root(**{"pairs": [(None, "Only Message")]})
        vals, _ = self._call({}, root)
        self.assertEqual(vals.get("note"), "Only Message")

        root = self._mk_root(
            **{
                "pairs": [
                    ("A1", "M1"),
                    ("A2", "M2"),
                ]
            }
        )
        vals, _ = self._call({}, root)
        self.assertEqual(vals.get("note"), "A1:\nM1\n\nA2:\nM2")

        root = self._mk_root(**{"pairs": [("", "Msg valid")]})
        vals, _ = self._call({}, root)
        self.assertEqual(vals.get("note"), "Msg valid")

    def test_parse_supplier_data_voxel(self):
        partner = self.ResPartner.create({"name": "Supplier X"})
        company = self.env["res.company"].create(
            {"name": "Test X", "partner_id": partner.id}
        )
        vals, errors = {}, []
        xml_root = self._mk_root(**{"supplier": True, "SupplierID": "SUP-1"})
        with patch.object(
            type(self.SaleOrder),
            "_get_partner_data_voxel",
            return_value={"name": "Supplier X", "vat": "123"},
        ) as gpd, patch.object(
            type(self.SaleOrder), "_parse_partner_data_voxel", return_value=partner
        ) as ppd:
            self.SaleOrder._parse_supplier_data_voxel(vals, xml_root, errors)
        self.assertEqual(vals.get("company_id"), company.id)
        self.assertEqual(errors, [])
        gpd.assert_called_once()
        ppd.assert_called_once()

        vals, errors = {}, []
        partner = self.ResPartner.create({"name": "Proveedor Y"})
        xml_root = self._mk_root(**{"supplier": True, "SupplierID": "SUP-2"})
        with patch.object(
            type(self.SaleOrder),
            "_get_partner_data_voxel",
            return_value={"name": "Supplier Y", "vat": "999"},
        ) as gpd, patch.object(
            type(self.SaleOrder), "_parse_partner_data_voxel", return_value=partner
        ) as ppd, patch.object(
            type(self.SaleOrder),
            "_get_voxel_msg_fields",
            return_value="<li>vat=999</li>",
        ) as gmf:
            self.SaleOrder._parse_supplier_data_voxel(vals, xml_root, errors)
        self.assertNotIn("company_id", vals)
        self.assertEqual(len(errors), 1)
        self.assertIn("<ul><li>vat=999</li></ul>", errors[0])
        gpd.assert_called_once()
        ppd.assert_called_once()
        gmf.assert_called_once()

        vals0 = {"keep": "me"}
        errs0 = []
        xml_root = etree.Element("Root")
        vals, errors = dict(vals0), list(errs0)
        self.SaleOrder._parse_supplier_data_voxel(vals, xml_root, errors)
        self.assertEqual(vals, vals0)
        self.assertEqual(errors, errs0)
