# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from werkzeug.exceptions import BadRequest, Unauthorized

from odoo import tools
from odoo.exceptions import UserError
from odoo.tests.common import SingleTransactionCase

from ..controllers.main import ImportController


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
        path = os.path.join(
            os.path.dirname(__file__), "examples", "UBL-Order-2.0-Example.xml"
        )
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
        order_ref = res.split(" ")[2]
        new_order = self.env["sale.order"].search([("name", "=", order_ref)])
        self.assertEqual(new_order.state, "draft")
        # Importing a 2nd time raises an error
        with self.assertRaisesRegex(
            UserError, "Sales order has already been imported before"
        ):
            with tools.mute_logger("odoo.addons.queue_job.models.base"):
                res = (
                    self.env["sale.order"]
                    .with_user(user)
                    .with_context(test_queue_job_no_delay=True)
                    .import_ubl_from_http(data)
                )

    def test_api_key_validity(self):
        """ Check auth key validity."""
        valid_key = self.env["auth.api.key"].create(
            {
                "name": "test_key",
                "user_id": self.env.ref("sale_order_import_ubl_http.user_endpoint").id,
            }
        )
        self.controller.check_api_key(self.env, valid_key.id)
        # Check non existing key
        with self.assertRaises(Unauthorized):
            self.controller.check_api_key(self.env, valid_key.id + 1)
        # Check key with incorrect user
        valid_key.user_id = self.env.user.id
        with self.assertRaises(Unauthorized):
            self.controller.check_api_key(self.env, valid_key.id)
