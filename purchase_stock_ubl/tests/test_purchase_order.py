# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.purchase_order_ubl.tests.test_ubl_generate \
    import TestUblOrder


class TestPurchaseOrder(TestUblOrder):

    def test_get_delivery_partner(self):

        order = self.env.ref('purchase.purchase_order_4')
        warehouse = order.picking_type_id.warehouse_id
        delivery_partner = order.get_delivery_partner()
        self.assertEqual(delivery_partner, warehouse.partner_id)

        res_partner_4 = self.env.ref('base.res_partner_4')
        order.dest_address_id = res_partner_4
        delivery_partner = order.get_delivery_partner()
        self.assertEqual(delivery_partner, order.dest_address_id)
        self.assertEqual(delivery_partner, res_partner_4)
