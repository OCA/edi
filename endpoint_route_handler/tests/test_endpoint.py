# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from functools import partial

from odoo.http import Controller

from ..registry import EndpointRegistry
from .common import CommonEndpoint


class TestEndpoint(CommonEndpoint):
    def tearDown(self):
        self.env["ir.http"]._clear_routing_map()
        EndpointRegistry.wipe_registry_for(self.env.cr.dbname)
        super().tearDown()

    def _make_new_route(self, **kw):
        vals = {
            "name": "Test custom route",
            "route": "/my/test/route",
            "request_method": "GET",
        }
        vals.update(kw)
        new_route = self.route_handler.new(vals)
        new_route._refresh_endpoint_data()
        return new_route

    def test_as_tool_base_data(self):
        new_route = self._make_new_route()
        self.assertEqual(new_route.route, "/my/test/route")
        first_hash = new_route.endpoint_hash
        self.assertTrue(first_hash)
        new_route.route += "/new"
        new_route._refresh_endpoint_data()
        self.assertNotEqual(new_route.endpoint_hash, first_hash)

    def test_as_tool_register_controller_no_default(self):
        new_route = self._make_new_route()
        # No specific controller
        with self.assertRaisesRegex(
            NotImplementedError, "No default endpoint handler defined."
        ):
            new_route._register_controller()

    def test_as_tool_register_controller(self):
        new_route = self._make_new_route()

        class TestController(Controller):
            def _do_something(self, route):
                return "ok"

        endpoint_handler = partial(TestController()._do_something, new_route.route)
        with self._get_mocked_request():
            new_route._register_controller(endpoint_handler=endpoint_handler)
            # Ensure the routing rule is registered
            rmap = self.env["ir.http"].routing_map()
            self.assertIn("/my/test/route", [x.rule for x in rmap._rules])
        # Ensure is updated when needed
        new_route.route += "/new"
        new_route._refresh_endpoint_data()
        with self._get_mocked_request():
            new_route._register_controller(endpoint_handler=endpoint_handler)
            rmap = self.env["ir.http"].routing_map()
            self.assertNotIn("/my/test/route", [x.rule for x in rmap._rules])
            self.assertIn("/my/test/route/new", [x.rule for x in rmap._rules])

    def test_as_tool_register_controller_dynamic_route(self):
        route = "/my/app/<model(app.model):foo>"
        new_route = self._make_new_route(route=route)

        class TestController(Controller):
            def _do_something(self, foo=None):
                return "ok"

        endpoint_handler = TestController()._do_something
        with self._get_mocked_request():
            new_route._register_controller(endpoint_handler=endpoint_handler)
            # Ensure the routing rule is registered
            rmap = self.env["ir.http"].routing_map()
            self.assertIn(route, [x.rule for x in rmap._rules])

    # TODO: test unregister
