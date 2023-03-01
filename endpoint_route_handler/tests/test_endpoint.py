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


def make_new_route(env, **kw):
    model = env["endpoint.route.handler.tool"]
    vals = {
        "name": "Test custom route",
        "route": "/my/test/route",
        "request_method": "GET",
    }
    vals.update(kw)
    new_route = model.new(vals)
    return new_route


class TestEndpoint(CommonEndpoint):
    def tearDown(self):
        self.env["ir.http"]._clear_routing_map()
        EndpointRegistry.wipe_registry_for(self.env.cr)
        super().tearDown()

    def test_as_tool_base_data(self):
        new_route = make_new_route(self.env)
        self.assertEqual(new_route.route, "/my/test/route")
        first_hash = new_route.endpoint_hash
        self.assertTrue(first_hash)
        new_route.route += "/new"
        self.assertNotEqual(new_route.endpoint_hash, first_hash)

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_single_controller(self):
        new_route = make_new_route(self.env)
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
        with self._get_mocked_request():
            new_route._register_single_controller(options=options, init=True)
            rmap = self.env["ir.http"]._clear_routing_map()
            rmap = self.env["ir.http"].routing_map()
            self.assertNotIn("/my/test/route", [x.rule for x in rmap._rules])
            self.assertIn("/my/test/route/new", [x.rule for x in rmap._rules])

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_controllers(self):
        new_route = make_new_route(self.env)
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
        with self._get_mocked_request():
            new_route._register_controllers(options=options, init=True)
            rmap = self.env["ir.http"]._clear_routing_map()
            rmap = self.env["ir.http"].routing_map()
            self.assertNotIn("/my/test/route", [x.rule for x in rmap._rules])
            self.assertIn("/my/test/route/new", [x.rule for x in rmap._rules])

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_as_tool_register_controllers_dynamic_route(self):
        route = "/my/app/<model(app.model):foo>"
        new_route = make_new_route(self.env, route=route)
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


class TestEndpointCrossEnv(CommonEndpoint):
    def setUp(self):
        super().setUp()
        self.env["ir.http"]._clear_routing_map()
        EndpointRegistry.wipe_registry_for(self.env.cr)

    @mute_logger("odoo.addons.base.models.ir_http", "odoo.modules.registry")
    def test_cross_env_consistency(self):
        """Ensure route updates are propagated to all envs."""
        route = "/my/app/<model(app.model):foo>"
        new_route = make_new_route(self.env, route=route)
        options = {
            "handler": {
                "klass_dotted_path": CTRLFake._path,
                "method_name": "custom_handler",
            }
        }

        env1 = self.env
        reg = EndpointRegistry.registry_for(self.env.cr)
        new_route._register_controllers(options=options)

        last_version0 = reg.last_version()
        with self._get_mocked_request():
            with new_rollbacked_env() as env2:
                # Load maps
                env1["ir.http"].routing_map()
                env2["ir.http"].routing_map()
                self.assertEqual(
                    env1["ir.http"]._endpoint_route_last_version, last_version0
                )
                self.assertEqual(
                    env2["ir.http"]._endpoint_route_last_version, last_version0
                )
                rmap = self.env["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])
                rmap = env2["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])

                # add new route
                route = "/my/new/<model(app.model):foo>"
                new_route = make_new_route(self.env, route=route)
                new_route._register_controllers(options=options)

                rmap = self.env["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])
                rmap = env2["ir.http"].routing_map()
                self.assertIn(route, [x.rule for x in rmap._rules])
                self.assertTrue(
                    env1["ir.http"]._endpoint_route_last_version > last_version0
                )
                self.assertTrue(
                    env2["ir.http"]._endpoint_route_last_version > last_version0
                )

    # TODO: test unregister
