# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from werkzeug.exceptions import BadRequest

from odoo import tools
from odoo.tests.common import SingleTransactionCase

from odoo.addons.sale_order_import_ubl_http.controllers.main import ImportController


class TestSaleOrderImportEndpoint(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.controller = ImportController()

    def test_invalid_data(self):
        data = "<xml>"
        with self.assertRaises(BadRequest):
            self.controller.check_data_to_import(self.env, data)

    def test_import_so_ubl(self):
        user = self.env.ref("sale_order_import_ubl_http.user_endpoint")
        path = os.path.join(os.path.dirname(__file__), "examples", "order_1.xml",)
        with open(path, "rb") as file:
            data = file.read()
        self.controller.check_data_to_import(self.env, data)
        data = data.decode("utf-8")
        with tools.mute_logger("odoo.addons.queue_job.models.base"):
            res = (
                self.env["sale.order"]
                .with_user(user)
                .with_context(test_queue_job_no_delay=True)
                .import_ubl_from_http(data)
            )
        order_id = int(res.split(" ")[-1])
        new_order = self.env["sale.order"].browse(order_id)
        self.assertEqual(new_order.state, "sale")
