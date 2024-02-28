# Copyright 2023 Camptocamp SA
# @author Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import os
import time

import responses
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from .common import CommonWebService, mock_cursor


class TestWebService(CommonWebService):
    @classmethod
    def _setup_records(cls):

        res = super()._setup_records()
        cls.url = "https://localhost.demo.odoo/"
        os.environ["SERVER_ENV_CONFIG"] = "\n".join(
            [
                "[webservice_backend.test_oauth2]",
                "auth_type = oauth2",
                "oauth2_clientid = some_client_id",
                "oauth2_client_secret = shh_secret",
                f"oauth2_token_url = {cls.url}oauth2/token",
                f"oauth2_audience = {cls.url}",
            ]
        )
        cls.webservice = cls.env["webservice.backend"].create(
            {
                "name": "WebService OAuth2",
                "tech_name": "test_oauth2",
                "auth_type": "oauth2",
                "protocol": "http",
                "url": cls.url,
                "content_type": "application/xml",
                "oauth2_clientid": "some_client_id",
                "oauth2_client_secret": "shh_secret",
                "oauth2_token_url": f"{cls.url}oauth2/token",
                "oauth2_audience": cls.url,
            }
        )
        return res

    def test_get_adapter_protocol(self):
        protocol = self.webservice._get_adapter_protocol()
        self.assertEqual(protocol, "http+oauth2")

    @responses.activate
    def test_fetch_token(self):
        duration = 3600
        expires_timestamp = time.time() + duration
        responses.add(
            responses.POST,
            f"{self.url}oauth2/token",
            json={
                "access_token": "cool_token",
                "expires_at": expires_timestamp,
                "expires_in": duration,
                "token_type": "Bearer",
            },
        )
        responses.add(responses.GET, f"{self.url}endpoint", body="OK")

        with mock_cursor(self.env.cr):
            result = self.webservice.call("get", url=f"{self.url}endpoint")
        self.webservice.refresh()
        self.assertTrue("cool_token" in self.webservice.oauth2_token)
        self.assertEqual(result, b"OK")

    @responses.activate
    def test_update_token(self):
        duration = 3600
        self.webservice.oauth2_token = json.dumps(
            {
                "access_token": "old_token",
                "expires_at": time.time() + 10,  # in the near future
                "expires_in": duration,
                "token_type": "Bearer",
            }
        )
        self.webservice.flush_model()

        expires_timestamp = time.time() + duration
        responses.add(
            responses.POST,
            f"{self.url}oauth2/token",
            json={
                "access_token": "cool_token",
                "expires_at": expires_timestamp,
                "expires_in": duration,
                "token_type": "Bearer",
            },
        )
        responses.add(responses.GET, f"{self.url}endpoint", body="OK")

        with mock_cursor(self.env.cr):
            result = self.webservice.call("get", url=f"{self.url}endpoint")
            self.env.cr.commit.assert_called_once_with()  # one call with no args

        self.webservice.refresh()
        self.assertTrue("cool_token" in self.webservice.oauth2_token)
        self.assertEqual(result, b"OK")

    @responses.activate
    def test_update_token_with_error(self):
        duration = 3600
        self.webservice.oauth2_token = json.dumps(
            {
                "access_token": "old_token",
                "expires_at": time.time() + 10,  # in the near future
                "expires_in": duration,
                "token_type": "Bearer",
            }
        )
        self.webservice.flush_model()

        responses.add(
            responses.POST,
            f"{self.url}oauth2/token",
            json={
                "error": "invalid_grant",
                "error_description": "invalid grant",
            },
            status=404,
        )
        responses.add(responses.GET, f"{self.url}endpoint", body="NOK", status=403)

        with mock_cursor(self.env.cr):
            with self.assertRaises(InvalidGrantError):
                self.webservice.call("get", url=f"{self.url}endpoint")
            self.env.cr.commit.assert_not_called()
            self.env.cr.close.assert_called_once_with()  # one call with no args

        self.webservice.refresh()
        self.assertTrue("old_token" in self.webservice.oauth2_token)
