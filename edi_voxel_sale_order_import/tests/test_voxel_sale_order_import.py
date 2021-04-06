# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import date, datetime

from odoo.modules.module import get_module_path
from odoo.tests import common


class TestVoxelSaleOrderImportCommon(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # This pricelist doesn't show the discount
        pricelist_test = cls.env["product.pricelist"].create(
            {"name": "pricelist test", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.company_test = cls.env["res.company"].create(
            {
                "name": "COMPANY TEST, S.A.",
                "street": "c/ Principal, s/n",
                "city": "Reus",
                "zip": "43111",
                "state_id": cls.env.ref("base.state_es_t").id,
                "country_id": cls.env.ref("base.es").id,
                "currency_id": pricelist_test.id,
                "vat": "ESA12345674",
            }
        )
        cls.customer_test = cls.env["res.partner"].create(
            {
                "name": "CUSTOMER TEST",
                "street": "Av Alcalde Pere Molas",
                "city": "Vila-seca",
                "zip": "43222",
                "ref": "F111",
                "state_id": cls.env.ref("base.state_es_t").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.product_test_1 = cls.env["product.product"].create(
            {"default_code": "111111", "name": "PRODUCT TEST"}
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
        module_path = get_module_path("edi_voxel_sale_order_import")
        file_path = os.path.join(module_path, "tests/voxel_xml", filename)
        with open(file_path) as file:
            content = file.read()
        # call method
        so_obj = self.env["sale.order"]
        return so_obj.create_document_from_xml(content, filename, self.company_test)


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
        self.assertEqual(sale_order.company_id, self.company_test)
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
