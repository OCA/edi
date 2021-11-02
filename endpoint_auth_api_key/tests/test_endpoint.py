# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import werkzeug

from odoo.tools.misc import mute_logger

from odoo.addons.endpoint.tests.common import CommonEndpoint


class TestEndpoint(CommonEndpoint):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.endpoint = cls.env.ref("endpoint_auth_api_key.endpoint_demo_1")
        cls.key_group = cls.env.ref("endpoint_auth_api_key.auth_api_key_group_demo")
        cls.api_key = cls.env.ref("endpoint_auth_api_key.auth_api_key_demo")
        cls.api_key2 = cls.env.ref("endpoint_auth_api_key.auth_api_key_demo2")

    @mute_logger("endpoint.endpoint")
    def test_endpoint_validate_request_no_key(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/api-key-test",
                "request_method": "GET",
            }
        )
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            with self._get_mocked_request(
                httprequest={"method": "GET"},
            ) as req:
                endpoint._validate_request(req)

    @mute_logger("endpoint.endpoint")
    def test_endpoint_validate_request_bad_key(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/api-key-test",
                "request_method": "GET",
            }
        )
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            with self._get_mocked_request(
                httprequest={"method": "GET"},
                request_attrs={"auth_api_key_id": self.api_key2.id},
            ) as req:
                endpoint._validate_request(req)

    def test_endpoint_validate_request_good_key(self):
        endpoint = self.endpoint.copy(
            {
                "route": "/api-key-test",
                "request_method": "GET",
            }
        )
        with self._get_mocked_request(
            httprequest={"method": "GET"},
            request_attrs={"auth_api_key_id": self.api_key.id},
        ) as req:
            endpoint._validate_request(req)
