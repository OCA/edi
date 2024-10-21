# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import TransactionCase


class TestOrderImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_display_name(self):
        sale_order = self.env.ref("sale.sale_order_1")
        name = sale_order.name + _(
            " Amount w/o tax: %(amount)s %(currency)s",
            amount=sale_order.amount_untaxed,
            currency=sale_order.currency_id.name,
        )
        so = (
            self.env["sale.order"]
            .with_context(sale_order_show_amount=True)
            .browse(sale_order.id)
        )
        so._compute_display_name()
        self.assertEqual(name, so.display_name)
