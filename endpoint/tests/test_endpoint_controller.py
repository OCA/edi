# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import os
import unittest

from odoo.tests.common import HttpCase
from odoo.tools.misc import mute_logger

# odoo.addons.base.models.res_users: Login successful for db:openerp_test login:admin from n/a
# endpoint.endpoint: Registered controller /demo/one/new (auth: user_endpoint)
# odoo.addons.endpoint.models.ir_http: DROPPED /demo/one
# odoo.addons.endpoint.models.ir_http: LOADED /demo/one/new
# odoo.addons.endpoint.models.ir_http: Endpoint routing map re-loaded


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class EndpointHttpCase(HttpCase):
    def setUp(self):
        super().setUp()

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
        response = self.url_open("/demo/one")
        self.assertEqual(response.status_code, 404)
        response = self.url_open("/demo/one/new")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

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
