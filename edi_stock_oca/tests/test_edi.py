# Copyright 2022 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import SavepointComponentRegistryCase
from odoo.addons.stock.tests.common import TestStockCommon


class EDIBackendTestCase(TestStockCommon, SavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        class StockPickingEventListenerDemo(Component):
            _name = "stock.picking.event.listener.demo"
            _inherit = "base.event.listener"

            def on_validate(self, picking):
                picking.name = "picking_done"

        StockPickingEventListenerDemo._build_component(cls.comp_registry)
        cls.comp_registry._cache.clear()
        cls.picking_in = cls.PickingObj.with_context(
            components_registry=cls.comp_registry
        ).create(
            {
                "picking_type_id": cls.picking_type_in,
                "location_id": cls.supplier_location,
                "location_dest_id": cls.stock_location,
            }
        )
        move_a = cls.MoveObj.create(
            {
                "name": cls.productA.name,
                "product_id": cls.productA.id,
                "product_uom_qty": 1,
                "product_uom": cls.productA.uom_id.id,
                "picking_id": cls.picking_in.id,
                "location_id": cls.supplier_location,
                "location_dest_id": cls.stock_location,
            }
        )
        cls.picking_in.refresh()
        cls.picking_in.action_confirm()
        cls.picking_in.action_assign()
        move_a.move_line_ids.qty_done = 4

    def test_validate_picking(self):
        self.picking_in.action_done()
        self.assertEqual(self.picking_in.name, "picking_done")
