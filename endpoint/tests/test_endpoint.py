# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import textwrap

import mock
import psycopg2
import werkzeug

from odoo import exceptions
from odoo.tools.misc import mute_logger

from .common import CommonEndpoint


class TestEndpoint(CommonEndpoint):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.endpoint = cls.env.ref("endpoint.endpoint_demo_1")

    @mute_logger("odoo.sql_db")
    def test_endpoint_unique(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "Endpoint",
                    "route": "/demo/one",
                    "exec_mode": "code",
                }
            )

    def test_endpoint_validation(self):
        with self.assertRaisesRegex(
            exceptions.UserError, r"you must provide a piece of code"
        ):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "Endpoint 2",
                    "route": "/demo/2",
                    "exec_mode": "code",
                    "request_method": "GET",
                    "auth_type": "user_endpoint",
                }
            )
        with self.assertRaisesRegex(
            exceptions.UserError, r"Request content type is required for POST and PUT."
        ):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "Endpoint 3",
                    "route": "/demo/3",
                    "exec_mode": "code",
                    "code_snippet": "foo = 1",
                    "request_method": "POST",
                    "auth_type": "user_endpoint",
                }
            )
        with self.assertRaisesRegex(
            exceptions.UserError, r"Request content type is required for POST and PUT."
        ):
            self.endpoint.request_method = "POST"

    def test_endpoint_find(self):
        self.assertEqual(
            self.env["endpoint.endpoint"]._find_endpoint("/demo/one"), self.endpoint
        )

    def test_endpoint_code_eval_full_response(self):
        with self._get_mocked_request() as req:
            result = self.endpoint._handle_request(req)
        resp = result["response"]
        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(resp.data, b"ok")

    def test_endpoint_code_eval_free_vals(self):
        self.endpoint.write(
            {
                "code_snippet": textwrap.dedent(
                    """
            result = {
                "payload": json.dumps({"a": 1, "b": 2}),
                "headers": [("content-type", "application/json")]
            }
            """
                )
            }
        )
        with self._get_mocked_request() as req:
            result = self.endpoint._handle_request(req)
        payload = result["payload"]
        self.assertEqual(json.loads(payload), {"a": 1, "b": 2})

    def test_endpoint_log(self):
        self.endpoint.write(
            {
                "code_snippet": textwrap.dedent(
                    """
            log("ciao")
            result = {"ok": True}
            """
                )
            }
        )
        with self._get_mocked_request() as req:
            # just test that logging does not break
            # as it creates a record directly via sql
            # and we cannot easily check the result
            self.endpoint._handle_request(req)
        self.env.cr.execute("DELETE FROM ir_logging")

    @mute_logger("endpoint.endpoint", "odoo.modules.registry")
    def test_endpoint_validate_request(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/wrong",
                "request_method": "POST",
                "request_content_type": "text/plain",
            }
        )
        with self.assertRaises(werkzeug.exceptions.UnsupportedMediaType):
            with self._get_mocked_request(httprequest={"method": "POST"}) as req:
                endpoint._validate_request(req)
        with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
            with self._get_mocked_request(
                httprequest={"method": "GET"},
                extra_headers=[("Content-type", "text/plain")],
            ) as req:
                endpoint._validate_request(req)

    @mute_logger("odoo.modules.registry")
    def test_routing(self):
        route, info, __ = self.endpoint._get_routing_info()
        self.assertEqual(route, "/demo/one")
        self.assertEqual(
            info,
            {
                "auth": "user_endpoint",
                "methods": ["GET"],
                "routes": ["/demo/one"],
                "type": "http",
                "csrf": False,
            },
        )
        endpoint = self.endpoint.copy(
            {
                "route": "/new/one",
                "request_method": "POST",
                "request_content_type": "text/plain",
                "auth_type": "public",
                "exec_as_user_id": self.env.user.id,
            }
        )
        __, info, __ = endpoint._get_routing_info()
        self.assertEqual(
            info,
            {
                "auth": "public",
                "methods": ["POST"],
                "routes": ["/new/one"],
                "type": "http",
                "csrf": False,
            },
        )
        # check prefix
        type(endpoint)._endpoint_route_prefix = "/foo"
        endpoint._compute_route()
        __, info, __ = endpoint._get_routing_info()
        self.assertEqual(
            info,
            {
                "auth": "public",
                "methods": ["POST"],
                "routes": ["/foo/new/one"],
                "type": "http",
                "csrf": False,
            },
        )
        type(endpoint)._endpoint_route_prefix = ""

    @mute_logger("odoo.modules.registry")
    def test_unlink(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/delete/this",
                "request_method": "POST",
                "request_content_type": "text/plain",
                "auth_type": "public",
                "exec_as_user_id": self.env.user.id,
            }
        )
        endpoint._handle_registry_sync()
        key = endpoint._endpoint_registry_unique_key()
        reg = endpoint._endpoint_registry
        self.assertEqual(reg._get_rule(key).route, "/delete/this")
        endpoint.unlink()
        self.assertEqual(reg._get_rule(key), None)

    @mute_logger("odoo.modules.registry")
    def test_archive(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/enable-disable/this",
                "request_method": "POST",
                "request_content_type": "text/plain",
                "auth_type": "public",
                "exec_as_user_id": self.env.user.id,
            }
        )
        endpoint._handle_registry_sync()
        self.assertTrue(endpoint.active)
        key = endpoint._endpoint_registry_unique_key()
        reg = endpoint._endpoint_registry
        self.assertEqual(reg._get_rule(key).route, "/enable-disable/this")
        endpoint.active = False
        endpoint._handle_registry_sync()
        self.assertEqual(reg._get_rule(key), None)

    def test_registry_sync(self):
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "New",
                "route": "/not/active/yet",
                "exec_mode": "code",
                "code_snippet": "foo = 1",
                "request_method": "GET",
                "auth_type": "user_endpoint",
            }
        )
        self.assertFalse(endpoint.registry_sync)
        key = endpoint._endpoint_registry_unique_key()
        reg = endpoint._endpoint_registry
        self.assertEqual(reg._get_rule(key), None)
        with mock.patch.object(type(self.env.cr.postcommit), "add") as mocked:
            endpoint.registry_sync = True
            partial_func = mocked.call_args[0][0]
            self.assertEqual(partial_func.args, ([endpoint.id],))
            self.assertEqual(
                partial_func.func.__name__, "_handle_registry_sync_post_commit"
            )

    def test_duplicate(self):
        endpoint = self.endpoint.copy()
        self.assertTrue(endpoint.route.endswith("/COPY_FIXME"))
