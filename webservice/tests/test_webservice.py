# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import responses
from requests import auth, exceptions as http_exceptions

from odoo import exceptions

from .common import CommonWebService


class TestWebService(CommonWebService):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.url = "http://localhost.demo.odoo/"
        cls.webservice = cls.env["webservice.backend"].create(
            {
                "name": "WebService",
                "protocol": "http",
                "url": cls.url,
                "content_type": "application/xml",
                "tech_name": "demo_ws",
                "auth_type": "none",
            }
        )
        return res

    def test_web_service_not_found(self):
        with self.assertRaises(http_exceptions.ConnectionError):
            self.webservice.call("get")

    def test_auth_validation(self):
        msg = (
            r"Webservice 'WebService' "
            r"requires 'Username & password' authentication. "
            r"However, the following field\(s\) are not valued: Username, Password"
        )
        with self.assertRaisesRegex(exceptions.UserError, msg):
            self.webservice.write(
                {
                    "auth_type": "user_pwd",
                }
            )

        msg = (
            r"Webservice 'WebService' "
            r"requires 'Username & password' authentication. "
            r"However, the following field\(s\) are not valued: Password"
        )
        with self.assertRaisesRegex(exceptions.UserError, msg):
            self.webservice.write({"auth_type": "user_pwd", "username": "user"})

        msg = (
            r"Webservice 'WebService' "
            r"requires 'API Key' authentication. "
            r"However, the following field\(s\) are not valued: API Key, API Key header"
        )
        with self.assertRaisesRegex(exceptions.UserError, msg):
            self.webservice.write(
                {
                    "auth_type": "api_key",
                }
            )

        msg = (
            r"Webservice 'WebService' "
            r"requires 'API Key' authentication. "
            r"However, the following field\(s\) are not valued: API Key header"
        )
        with self.assertRaisesRegex(exceptions.UserError, msg):
            self.webservice.write(
                {
                    "auth_type": "api_key",
                    "api_key": "foo",
                }
            )

    @responses.activate
    def test_web_service_get(self):
        responses.add(responses.GET, self.url, body="{}")
        result = self.webservice.call("get")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )

    @responses.activate
    def test_web_service_get_url_combine(self):
        endpoint = "api/test"
        responses.add(responses.GET, self.url + endpoint, body="{}")
        result = self.webservice.call("get", url="api/test")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )

    @responses.activate
    def test_web_service_get_url_combine_full_url(self):
        endpoint = "api/test"
        responses.add(responses.GET, self.url + endpoint, body="{}")
        result = self.webservice.call("get", url="http://localhost.demo.odoo/api/test")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )

    @responses.activate
    def test_web_service_post(self):
        responses.add(responses.POST, self.url, body="{}")
        result = self.webservice.call("post", data="demo_response")
        self.assertEqual(result, b"{}")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "demo_response")

    @responses.activate
    def test_web_service_put(self):
        responses.add(responses.PUT, self.url, body="{}")
        result = self.webservice.call("put", data="demo_response")
        self.assertEqual(result, b"{}")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "demo_response")

    @responses.activate
    def test_web_service_backend_username(self):
        self.webservice.write(
            {"auth_type": "user_pwd", "username": "user", "password": "pass"}
        )
        responses.add(responses.GET, self.url, body="{}")
        result = self.webservice.call("get")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        data = auth._basic_auth_str("user", "pass")
        self.assertEqual(responses.calls[0].request.headers["Authorization"], data)

    @responses.activate
    def test_web_service_username(self):
        self.webservice.write(
            {"auth_type": "user_pwd", "username": "user", "password": "pass"}
        )
        responses.add(responses.GET, self.url, body="{}")
        result = self.webservice.call("get", auth=("user2", "pass2"))
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        data = auth._basic_auth_str("user2", "pass2")
        self.assertEqual(responses.calls[0].request.headers["Authorization"], data)

    @responses.activate
    def test_web_service_backend_api_key(self):
        self.webservice.write(
            {"auth_type": "api_key", "api_key": "123xyz", "api_key_header": "Api-Key"}
        )
        responses.add(responses.POST, self.url, body="{}")
        result = self.webservice.call("post")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.headers["Api-Key"], "123xyz")

    @responses.activate
    def test_web_service_headers(self):
        responses.add(responses.GET, self.url, body="{}")
        result = self.webservice.call("get", headers={"demo_header": "HEADER"})
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.headers["demo_header"], "HEADER")

    @responses.activate
    def test_web_service_call_args(self):
        url = "https://custom.url"
        responses.add(responses.POST, url, body="{}")
        result = self.webservice.call(
            "post", url=url, headers={"demo_header": "HEADER"}
        )
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.headers["demo_header"], "HEADER")

        url = self.url + "custom/path"
        self.webservice.url += "{endpoint}"
        responses.add(responses.POST, url, body="{}")
        result = self.webservice.call(
            "post",
            url_params={"endpoint": "custom/path"},
            headers={"demo_header": "HEADER"},
        )
        self.assertEqual(result, b"{}")
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.headers["demo_header"], "HEADER")
