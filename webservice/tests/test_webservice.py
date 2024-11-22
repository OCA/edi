# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import httpretty
from requests import auth, exceptions as http_exceptions

from odoo import exceptions

from .common import CommonWebService


class TestWebService(CommonWebService):
    def _setup_records(self):
        res = super(TestWebService, self)._setup_records()
        self.url = "https://localhost.demo.odoo/"
        self.webservice = self.env["webservice.backend"].create(
            {
                "name": "WebService",
                "protocol": "http",
                "url": self.url,
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
        with self.assertRaisesRegex(exceptions.ValidationError, msg):
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
        with self.assertRaisesRegex(exceptions.ValidationError, msg):
            self.webservice.write({"auth_type": "user_pwd", "username": "user"})

        msg = (
            r"Webservice 'WebService' "
            r"requires 'API Key' authentication. "
            r"However, the following field\(s\) are not valued: API Key, API Key header"
        )
        with self.assertRaisesRegex(exceptions.ValidationError, msg):
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
        with self.assertRaisesRegex(exceptions.ValidationError, msg):
            self.webservice.write(
                {
                    "auth_type": "api_key",
                    "api_key": "foo",
                }
            )

    @httpretty.activate
    def test_web_service_get(self):
        httpretty.register_uri(httpretty.GET, self.url, body="{}")
        result = self.webservice.call("get")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )

    @httpretty.activate
    def test_web_service_post(self):
        httpretty.register_uri(httpretty.POST, self.url, body="{}")
        result = self.webservice.call("post", data="demo_response")
        self.assertEqual(result, b"{}")
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(httpretty.latest_requests()[0].body, b"demo_response")

    @httpretty.activate
    def test_web_service_put(self):
        httpretty.register_uri(httpretty.PUT, self.url, body="{}")
        result = self.webservice.call("put", data="demo_response")
        self.assertEqual(result, b"{}")
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(httpretty.latest_requests()[0].body, b"demo_response")

    @httpretty.activate
    def test_web_service_backend_username(self):
        self.webservice.write(
            {"auth_type": "user_pwd", "username": "user", "password": "pass"}
        )
        httpretty.register_uri(httpretty.GET, self.url, body="{}")
        result = self.webservice.call("get")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        data = auth._basic_auth_str("user", "pass")
        self.assertEqual(httpretty.latest_requests()[0].headers["Authorization"], data)

    @httpretty.activate
    def test_web_service_username(self):
        self.webservice.write(
            {"auth_type": "user_pwd", "username": "user", "password": "pass"}
        )
        httpretty.register_uri(httpretty.GET, self.url, body="{}")
        result = self.webservice.call("get", auth=("user2", "pass2"))
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        data = auth._basic_auth_str("user2", "pass2")
        self.assertEqual(httpretty.latest_requests()[0].headers["Authorization"], data)

    @httpretty.activate
    def test_web_service_backend_api_key(self):
        self.webservice.write(
            {"auth_type": "api_key", "api_key": "123xyz", "api_key_header": "Api-Key"}
        )
        httpretty.register_uri(httpretty.POST, self.url, body="{}")
        result = self.webservice.call("post")
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(httpretty.latest_requests()[0].headers["Api-Key"], "123xyz")

    @httpretty.activate
    def test_web_service_headers(self):
        httpretty.register_uri(httpretty.GET, self.url, body="{}")
        result = self.webservice.call("get", headers={"demo_header": "HEADER"})
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(
            httpretty.latest_requests()[0].headers["demo_header"],
            "HEADER"
        )

    @httpretty.activate
    def test_web_service_call_args(self):
        url = "https://custom.url"
        httpretty.register_uri(httpretty.POST, url, body="{}")
        result = self.webservice.call(
            "post", url=url, headers={"demo_header": "HEADER"}
        )
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(
            httpretty.latest_requests()[0].headers["demo_header"],
            "HEADER"
        )

        url = self.url + "custom/path"
        self.webservice.url += "{endpoint}"
        httpretty.register_uri(httpretty.POST, url, body="{}")
        result = self.webservice.call(
            "post",
            url_params={"endpoint": "custom/path"},
            headers={"demo_header": "HEADER"},
        )
        self.assertEqual(result, b"{}")
        self.assertEqual(len(httpretty.latest_requests()), 2)
        self.assertEqual(
            httpretty.latest_requests()[0].headers["Content-Type"], "application/xml"
        )
        self.assertEqual(
            httpretty.latest_requests()[0].headers["demo_header"],
            "HEADER"
        )
