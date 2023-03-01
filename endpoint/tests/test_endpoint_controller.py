# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import os
from unittest import skipIf

from odoo.tests.common import HttpSavepointCase
from odoo.tools.misc import mute_logger


@skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class EndpointHttpCase(HttpSavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force sync for demo records
        cls.env["endpoint.endpoint"].search([])._handle_registry_sync()

    def tearDown(self):
        self.env["ir.http"]._clear_routing_map()
        super().tearDown()

    def test_call1(self):
        response = self.url_open("/demo/one")
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open("/demo/one")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_call_route_update(self):
        # Ensure that a route that gets updated is not available anymore
        self.authenticate("admin", "admin")
        endpoint = self.env.ref("endpoint.endpoint_demo_1")
        endpoint.route += "/new"
        # force sync
        endpoint._handle_registry_sync()
        response = self.url_open("/demo/one")
        self.assertEqual(response.status_code, 404)
        response = self.url_open("/demo/one/new")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
        # Archive it
        endpoint.active = False
        response = self.url_open("/demo/one/new")
        self.assertEqual(response.status_code, 404)
        endpoint.active = True
        response = self.url_open("/demo/one/new")
        self.assertEqual(response.status_code, 200)

    def test_call2(self):
        response = self.url_open("/demo/as_demo_user")
        self.assertEqual(response.content, b"My name is: Marc Demo")

    def test_call3(self):
        response = self.url_open("/demo/json_data")
        data = json.loads(response.content.decode())
        self.assertEqual(data, {"a": 1, "b": 2})

    @mute_logger("endpoint.endpoint")
    def test_call4(self):
        response = self.url_open("/demo/raise_validation_error")
        self.assertEqual(response.status_code, 400)

    def test_call5(self):
        response = self.url_open("/demo/none")
        self.assertEqual(response.status_code, 404)

    def test_call6(self):
        response = self.url_open("/demo/value_from_request?your_name=JonnyTest")
        self.assertEqual(response.content, b"JonnyTest")

    def test_call7(self):
        response = self.url_open("/demo/bad_method", data="ok")
        self.assertEqual(response.status_code, 405)
