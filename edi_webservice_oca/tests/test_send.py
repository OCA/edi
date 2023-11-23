# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import responses

from odoo import exceptions

from .common import TestEDIWebserviceBase


class TestSend(TestEDIWebserviceBase):
    @classmethod
    def _setup_records(cls):
        result = super()._setup_records()
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
        return result

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
        url = "https://foo.test/push/here"
        responses.add(responses.POST, url, body="{}")
        component = self.backend._get_component(self.record, "send")
        result = component.send()
        self.assertEqual(result, b"{}")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "This is a simple file")
