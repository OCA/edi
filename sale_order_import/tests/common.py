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
        cls.wiz_model = cls.env["sale.order.import"]
        cls.partner = cls.env["res.partner"].create({"name": "SO Test"})

    def read_test_file(self, filename, mode="r", as_b64=False):
        path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
        with open(path, mode) as thefile:
            content = thefile.read()
            return content if not as_b64 else base64.b64encode(content)
