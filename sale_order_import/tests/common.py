# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import os

from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env["res.config.settings"].create(
            {"group_product_pricelist": True}
        ).set_values()
        cls.wiz_model = cls.env["sale.order.import"]
        curr = cls.env.ref("base.USD")
        curr.active = True
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": curr.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "SO Test",
                "email": "so.import.test@example.com",
            }
        )
        cls.partner.property_product_pricelist = cls.pricelist
        cls.env["product.template"].create(
            [
                {
                    "name": "Test Product 8888",
                    "default_code": "FURN_8888",
                    "list_price": 12.42,
                    "type": "consu",
                    "uom_id": cls.env.ref("uom.product_uom_unit").id,
                },
                {
                    "name": "Test Product 9999",
                    "default_code": "FURN_9999",
                    "list_price": 1.42,
                    "type": "consu",
                    "uom_id": cls.env.ref("uom.product_uom_unit").id,
                },
                {
                    "name": "Test Product 7777",
                    "default_code": "FURN_7777",
                    "list_price": 3.0,
                    "type": "consu",
                    "uom_id": cls.env.ref("uom.product_uom_unit").id,
                },
            ]
        )

    def read_test_file(self, filename, mode="r", as_b64=False):
        path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
        with open(path, mode) as thefile:
            content = thefile.read()
            return content if not as_b64 else base64.b64encode(content)
