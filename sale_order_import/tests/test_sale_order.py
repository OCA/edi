# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestOrderImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "Display Name Customer"})
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        cls.sale_order = sale_form.save()

    def test_display_name(self):
        expected_name = self.sale_order.name + self.env._(
            " Amount w/o tax: %(amount)s %(currency)s",
            amount=self.sale_order.amount_untaxed,
            currency=self.sale_order.currency_id.name,
        )
        so = self.sale_order.with_context(sale_order_show_amount=True)
        so.invalidate_recordset()
        self.assertEqual(so.display_name, expected_name)
