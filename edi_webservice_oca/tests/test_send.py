# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import responses

from odoo import exceptions

from ..components.send import EDIWebserviceSendHTTPException
from .common import TestEDIWebserviceBase


class TestSend(TestEDIWebserviceBase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.ws_backend = cls.backend.webservice_backend_id
        cls.settings1 = """
        components:
          send:
            usage: webservice.send
            work_ctx:
              webservice:
                _no_method: post
                pargs:
                  - foo
                  - bar
                kwargs:
                  random: 1
                  url_params:
                    endpoint: push/here
        """
        cls.settings2 = """
        components:
          send:
            usage: webservice.send
            work_ctx:
              webservice:
                method: post
                kwargs:
                  url_params:
                    endpoint: push/here
        """
        cls.record.type_id.set_settings(cls.settings1)
        cls.a_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "foo",
                    "login": "a_user",
                    "email": "foo@bar.com",
                    "groups_id": [
                        (
                            6,
                            0,
                            (cls.env.ref("base.group_user")).ids,
                        )
                    ],
                }
            )
        )

    def test_find_component(self):
        component = self.backend._get_component(self.record, "send")
        self.assertEqual(component._name, "edi.webservice.send")

    def test_component_settings(self):
        component = self.backend._get_component(self.record, "send")
        self.assertEqual(
            component.ws_settings,
            {
                "_no_method": "post",
                "pargs": ["foo", "bar"],
                "kwargs": {
                    "random": 1,
                    "url_params": {
                        "endpoint": "push/here",
                    },
                },
            },
        )

    def test_component_no_method(self):
        component = self.backend._get_component(self.record, "send")
        msg = "`method` is required in `webservice` type settings"
        with self.assertRaisesRegex(exceptions.UserError, msg):
            component._get_call_params()

    def test_component_params(self):
        self.record.type_id.set_settings(self.settings2)
        component = self.backend._get_component(self.record, "send")
        method, pargs, kwargs = component._get_call_params()
        self.assertEqual(method, "post")
        self.assertEqual(len(kwargs), 2)
        self.assertEqual(kwargs["data"], "This is a simple file")
        self.assertEqual(kwargs["url_params"], {"endpoint": "push/here"})

    @responses.activate
    def test_component_send(self):
        self.record.type_id.set_settings(self.settings2)
        # Internal user should be able to call the third party webservice
        # without read access (no ir.access.model records)
        # on `webservice.backend` model which store credentials
        record = self.record.with_user(self.a_user)
        backend = self.backend.with_user(self.a_user)

        url = "https://foo.test/push/here"
        responses.add(responses.POST, url, body="{}")
        component = backend._get_component(record, "send")
        result = component.send()
        self.assertEqual(result, b"{}")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "This is a simple file")

    @responses.activate
    def test_component_send_raise_http_error(self):
        self.record.type_id.set_settings(self.settings2)
        record = self.record.with_user(self.a_user)
        backend = self.backend.with_user(self.a_user)

        url = "https://foo.test/push/here"
        responses.add(responses.POST, url, status=404)
        component = backend._get_component(record, "send")
        with self.assertRaises(EDIWebserviceSendHTTPException):
            component.send()
