# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import _


class TestSaleOrder(TransactionCase):
    def test_name_get(self):
        sale_order = self.env.ref('sale.sale_order_1')
        name = sale_order.name + _(' Amount w/o tax: %s %s)') % (
            sale_order.amount_untaxed, sale_order.currency_id.name)
        so = self.env['sale.order'].with_context(
            sale_order_show_amount=True
        )
        name_get_res = so.search([
            ('id', '=', sale_order.id)
        ]).name_get()
        self.assertEqual(name, name_get_res[0][1])
