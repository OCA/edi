# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest

from odoo.tests.common import HttpCase

from ..registry import EndpointRegistry
from .fake_controllers import TestController


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class EndpointHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.route_handler = self.env["endpoint.route.handler.tool"]

    def tearDown(self):
        EndpointRegistry.wipe_registry_for(self.env.cr)
        self.env["ir.http"]._clear_routing_map()
        super().tearDown()

    def _make_new_route(self, options=None, **kw):
        vals = {
            "name": "Test custom route",
            "request_method": "GET",
        }
        vals.update(kw)
        new_route = self.route_handler.new(vals)
        new_route._register_controllers(options=options)
        return new_route

    def test_call(self):
        options = {
            "handler": {
                "klass_dotted_path": TestController._path,
                "method_name": "_do_something1",
            }
        }
        self._make_new_route(route="/my/test/<string:foo>", options=options)
        route = "/my/test/working"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Got: working")

    def test_call_advanced_endpoint_handler(self):
        options = {
            "handler": {
                "klass_dotted_path": TestController._path,
                "method_name": "_do_something2",
                "default_pargs": ("DEFAULT",),
            }
        }
        self._make_new_route(route="/my/advanced/test/<string:foo>", options=options)
        route = "/my/advanced/test/working"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"DEFAULT -> got: working")
