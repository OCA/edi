# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from contextlib import contextmanager

import odoo
from odoo.tools import mute_logger

from ..registry import EndpointRegistry
from .common import CommonEndpoint
from .fake_controllers import CTRLFake


@contextmanager
def new_rollbacked_env():
    # Borrowed from `component`
    registry = odoo.registry(odoo.tests.common.get_db_name())
    uid = odoo.SUPERUSER_ID
    cr = registry.cursor()
    try:
        yield odoo.api.Environment(cr, uid, {})
    finally:
        cr.rollback()  # we shouldn't have to commit anything
        cr.close()


class TestEndpoint(CommonEndpoint):
    def tearDown(self):
        self.env["ir.http"]._clear_routing_map()
        EndpointRegistry.wipe_registry_for(self.env.cr)
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

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_single_controller(self):
        new_route = self._make_new_route()
        options = {
            "handler": {
                "klass_dotted_path": CTRLFake._path,
                "method_name": "custom_handler",
            }
        }

        with self._get_mocked_request():
            new_route._register_single_controller(options=options, init=True)
            # Ensure the routing rule is registered
            rmap = self.env["ir.http"].routing_map()
            self.assertIn("/my/test/route", [x.rule for x in rmap._rules])

        # Ensure is updated when needed
        new_route.route += "/new"
        new_route._refresh_endpoint_data()
        with self._get_mocked_request():
            new_route._register_single_controller(options=options, init=True)
            rmap = self.env["ir.http"]._clear_routing_map()
            rmap = self.env["ir.http"].routing_map()
            self.assertNotIn("/my/test/route", [x.rule for x in rmap._rules])
            self.assertIn("/my/test/route/new", [x.rule for x in rmap._rules])

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_controllers(self):
        new_route = self._make_new_route()
        options = {
            "handler": {
                "klass_dotted_path": CTRLFake._path,
                "method_name": "custom_handler",
            }
        }

        with self._get_mocked_request():
            new_route._register_controllers(options=options, init=True)
            # Ensure the routing rule is registered
            rmap = self.env["ir.http"].routing_map()
            self.assertIn("/my/test/route", [x.rule for x in rmap._rules])

        # Ensure is updated when needed
        new_route.route += "/new"
        new_route._refresh_endpoint_data()
        with self._get_mocked_request():
            new_route._register_controllers(options=options, init=True)
            rmap = self.env["ir.http"]._clear_routing_map()
            rmap = self.env["ir.http"].routing_map()
            self.assertNotIn("/my/test/route", [x.rule for x in rmap._rules])
            self.assertIn("/my/test/route/new", [x.rule for x in rmap._rules])

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_controllers_dynamic_route(self):
        route = "/my/app/<model(app.model):foo>"
        new_route = self._make_new_route(route=route)

        options = {
            "handler": {
                "klass_dotted_path": CTRLFake._path,
                "method_name": "custom_handler",
            }
        }

        with self._get_mocked_request():
            new_route._register_controllers(options=options, init=True)
            # Ensure the routing rule is registered
            rmap = self.env["ir.http"].routing_map()
            self.assertIn(route, [x.rule for x in rmap._rules])

    @mute_logger("odoo.addons.base.models.ir_http", "odoo.modules.registry")
    def test_cross_env_consistency(self):
        """Ensure route updates are propagated to all envs."""
        route = "/my/app/<model(app.model):foo>"
        new_route = self._make_new_route(route=route)

        options = {
            "handler": {
                "klass_dotted_path": CTRLFake._path,
                "method_name": "custom_handler",
            }
        }

        env1 = self.env
        with self._get_mocked_request():
            with new_rollbacked_env() as env2:
                # Load maps
                env1["ir.http"].routing_map()
                env2["ir.http"].routing_map()
                # Register route in current env.
                # By using `init=True` we don't trigger env signals
                # (simulating when the registry is loaded for the 1st time
                # by `_register_hook`).
                # In this case we expect the test to fail
                # as there's no propagation to the other env.
                new_route._register_controllers(options=options, init=True)
                rmap = self.env["ir.http"].routing_map()
                self.assertNotIn(route, [x.rule for x in rmap._rules])
                rmap = env2["ir.http"].routing_map()
                self.assertNotIn(route, [x.rule for x in rmap._rules])
                # Now w/out init -> works
                new_route._register_controllers(options=options)
                rmap = self.env["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])
                rmap = env2["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])

    # TODO: test unregister
