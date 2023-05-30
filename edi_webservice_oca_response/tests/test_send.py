# Copyright 2022 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import responses

from odoo.addons.edi_webservice_oca.tests.common import TestEDIWebserviceBase


class TestSend(TestEDIWebserviceBase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.ws_backend = cls.backend.webservice_backend_id
        cls.settings = """
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
        cls.record.edi_exchange_state = "output_pending"

    @responses.activate
    def test_component_send_save_results_on_success(self):
        self.record.type_id.set_settings(self.settings)
        url = "https://foo.test/push/here"
        response = "{'result': 'ok'}"
        responses.add(responses.POST, url, body=response)
        self.backend._check_output_exchange_sync()
        self.assertEqual(self.record.edi_exchange_state, "output_sent")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "This is a simple file")
        self.assertEqual(
            self.record._get_file_content(field_name="ws_response_content"), response
        )

    @responses.activate
    def test_component_send_save_results_on_error(self):
        self.record.type_id.set_settings(self.settings)
        url = "https://foo.test/push/here"
        response = (
            "{'error': 'something that details what went wrong to help investigations'}"
        )
        responses.add(
            responses.POST,
            url,
            body=response,
            status=401,
        )
        self.backend._check_output_exchange_sync()
        self.assertEqual(self.record.edi_exchange_state, "output_error_on_send")
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "This is a simple file")
        self.assertEqual(
            self.record._get_file_content(field_name="ws_response_content"), response
        )
