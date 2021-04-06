# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.edi_voxel_sale_order_import.tests.test_voxel_sale_order_import import (
    TestVoxelSaleOrderImportCommon,
)


class TestVoxelSaleSecondaryUnit(TestVoxelSaleOrderImportCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Secondary UoM Boxes (for defined cls.product_test_1 product)
        # mapped to 'Cajas' voxel code, so that when importing it is set
        # in 'order line 1' instead of 'Boxes' standard UoM ('uom.uom')
        cls.boxes_secondary_uom = cls.env["product.secondary.unit"].create(
            {
                "product_tmpl_id": cls.product_test_1.product_tmpl_id.id,
                "name": "Boxes",
                "code": "Boxes",
                "voxel_code": "Cajas",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "factor": 20,
            }
        )

    def test_create_document_from_xml(self):
        sale_order = self._create_document_from_test_file()
        # roduct_uom_qty of the first order line is 40 instead of 1,
        # because the secondary UoM 'Boxes' is matched and set, so
        # 'Secondary Qty' is also 2.
        so_line = sale_order.order_line[0]
        self.assertEqual(so_line.secondary_uom_id, self.boxes_secondary_uom)
        self.assertEqual(so_line.secondary_uom_qty, 2)
        self.assertEqual(so_line.product_uom, self.env.ref("uom.product_uom_unit"))
        self.assertEqual(so_line.product_uom_qty, 40)
        # Assert there is no Secondary UoM matched, so it is False
        so_line = sale_order.order_line[1]
        self.assertFalse(so_line.secondary_uom_id)
        self.assertEqual(so_line.secondary_uom_qty, 0.0)
        self.assertEqual(so_line.product_uom, self.env.ref("uom.product_uom_unit"))
        self.assertEqual(so_line.product_uom_qty, 2)
