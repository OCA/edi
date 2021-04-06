# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.edi_voxel_stock_picking.tests.test_voxel_stock_picking import (
    TestVoxelStockPickingCommon,
)


class TestVoxelStockPickingSecondaryUnit(TestVoxelStockPickingCommon):
    @classmethod
    def _create_sale_order(cls):
        sale_order = super()._create_sale_order()
        secondary_uom = cls.env["product.secondary.unit"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "code": "boxes",
                "name": "Boxes",
                "voxel_code": "Cajas",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "factor": 20,
            }
        )
        cls.env.user.groups_id += cls.env.ref("uom.group_uom")
        with Form(sale_order) as so_form:
            with so_form.order_line.edit(0) as so_line_form:
                so_line_form.secondary_uom_id = secondary_uom
                so_line_form.secondary_uom_qty = 2
        return sale_order

    def test_get_report_values(self):
        # Get report data
        report_edi_obj = self.env[
            "report.edi_voxel_stock_picking.template_voxel_picking"
        ]
        report_data = report_edi_obj._get_report_values(self.picking.ids)
        # Check product data
        self.assertListEqual(report_data["products"], self._get_products_data())

    def _get_products_data(self):
        return [
            {
                "product": {
                    "SupplierSKU": "DC_001",
                    "CustomerSKU": "1234567891234",
                    "Item": "Product 1 (test)",
                    "Qty": "2.0",
                    "MU": "Cajas",
                },
            },
            {
                "product": {
                    "SupplierSKU": "DC_002",
                    "CustomerSKU": False,
                    "Item": "Product 2 (test)",
                    "Qty": "1.0",
                    "MU": "Unidades",
                    "TraceabilityList": [
                        {
                            "BatchNumber": "LOT01",
                            "ExpirationDate": "2020-01-01T12:05:23",
                            "Quantity": 1.0,
                        }
                    ],
                },
            },
        ]
