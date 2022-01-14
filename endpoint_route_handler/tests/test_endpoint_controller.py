# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest
from functools import partial

from odoo.http import Controller
from odoo.tests.common import HttpCase

from ..registry import EndpointRegistry


class TestController(Controller):
    def _do_something1(self, foo=None):
        return f"Got: {foo}"

    def _do_something2(self, default_arg, foo=None):
        return f"{default_arg} -> got: {foo}"


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class EndpointHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.route_handler = self.env["endpoint.route.handler"]

    def tearDown(self):
        EndpointRegistry.wipe_registry_for(self.env.cr.dbname)
        self.env["ir.http"]._clear_routing_map()
        super().tearDown()

    def _make_new_route(self, register=True, **kw):
        vals = {
            "name": "Test custom route",
            "request_method": "GET",
        }
        vals.update(kw)
        new_route = self.route_handler.new(vals)
        new_route._refresh_endpoint_data()
        return new_route

    def _register_controller(self, route_obj, endpoint_handler=None):
        endpoint_handler = endpoint_handler or TestController()._do_something1
        route_obj._register_controller(endpoint_handler=endpoint_handler)

    def test_call(self):
        new_route = self._make_new_route(route="/my/test/<string:foo>")
        self._register_controller(new_route)

        route = "/my/test/working"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Got: working")

    def test_call_advanced_endpoint_handler(self):
        new_route = self._make_new_route(route="/my/advanced/test/<string:foo>")
        endpoint_handler = partial(TestController()._do_something2, "DEFAULT")
        self._register_controller(new_route, endpoint_handler=endpoint_handler)

        route = "/my/advanced/test/working"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"DEFAULT -> got: working")
