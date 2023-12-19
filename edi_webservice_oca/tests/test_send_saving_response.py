# Copyright 2023 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from contextlib import contextmanager
from unittest import mock

import responses
from odoo_test_helper import FakeModelLoader

from odoo import models

from odoo.addons.queue_job.exception import RetryableJobError

from .common import TestEDIWebserviceBase


class TestSend(TestEDIWebserviceBase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.ws_backend = cls.backend.webservice_backend_id
        cls.ws_backend.save_response = True
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

        @contextmanager
        def _consumer_record_no_new_env(self, record, new_cursor=True):
            yield record

        cls._consumer_record_no_new_env = _consumer_record_no_new_env

    @responses.activate
    def test_component_send_save_results_on_success(self):
        self.record.type_id.set_settings(self.settings)
        url = "https://foo.test/push/here"
        response = "{'result': 'ok'}"
        responses.add(responses.POST, url, body=response)
        with mock.patch(
            "odoo.addons.webservice.models.webservice_backend."
            "WebserviceBackend._consumer_record_env",
            side_effect=self._consumer_record_no_new_env,
        ):
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
    def test_component_send_save_results_on_http_error_without_changing_exchange_state(
        self,
    ):
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

        with mock.patch(
            "odoo.addons.webservice.models.webservice_backend."
            "WebserviceBackend._consumer_record_env",
            side_effect=self._consumer_record_no_new_env,
        ) as mo:
            with self.assertRaisesRegex(RetryableJobError, "Unauthorized"):
                self.backend._check_output_exchange_sync()
        mo.assert_called_once_with(self.record, new_cursor=True)
        self.assertEqual(self.record.edi_exchange_state, "output_pending")

    def test_not_http_exception(self):
        self.record.type_id.set_settings(self.settings)
        self.record.ws_response_status_code = 200
        self.record._set_file_content(
            "first call content", field_name="ws_response_content"
        )

        with mock.patch(
            "odoo.addons.webservice.models.webservice_backend."
            "WebserviceBackend._consumer_record_env",
            side_effect=self._consumer_record_no_new_env,
        ):
            with mock.patch(
                "odoo.addons.webservice.components.request_adapter."
                "BaseRestRequestsAdapter._get_url",
                side_effect=Exception("Not an HTTPError"),
            ):
                with self.assertRaisesRegex(Exception, "Not an HTTPError"):
                    self.backend._check_output_exchange_sync()

        self.assertFalse(self.record.ws_response_status_code)
        self.assertFalse(
            self.record._get_file_content(field_name="ws_response_content")
        )

    def test_ws_response_content_filename(self):
        self.record.exchange_filename = "test.json"
        self.assertEqual(self.record.ws_response_content_filename, "response_test.json")


class TestWebServiceSendHandledErrorChangingExchangeState(TestEDIWebserviceBase):
    """This test demonstrate how to force state of exchange record
    even we get HTTP ERROR, because webservice module open a new transaction
    to change state of the consumer record in case of status code != 200 we
    can't use the swapping method.

    Choice have to be made at developement level to decide what to do according
    the current record type
    """

    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.addClassCleanup(cls.loader.restore_registry)
        cls.loader.backup_registry()
        cls.edi_exchange_state_changed = False

        class EDIExchangeRecord(models.Model):
            _name = "edi.exchange.record"
            _inherit = "edi.exchange.record"

            def _save_ws_response(self, content, status_code):
                super()._save_ws_response(content, status_code)
                if (
                    self.backend_id.webservice_backend_id.save_response
                    and status_code != 200
                ):
                    self.edi_exchange_state = "output_error_on_send"
                    # because we are in unittest we have only one transaction
                    # as we are creating the exchange record in this transaction
                    # we can't really instantiate a new transaction
                    # So this edi_exchange_state get overwritten by
                    # the edi_oca.models.edi_backend.EDIBackend.exchange_send
                    # finally clause that would be rollback in production server
                    # so use this attribute to assert state has been changed
                    cls.edi_exchange_state_changed = True

        cls.loader.update_registry((EDIExchangeRecord,))

        cls.ws_backend = cls.backend.webservice_backend_id
        cls.ws_backend.save_response = True
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

        @contextmanager
        def _consumer_record_no_new_env(self, record, new_cursor=True):
            yield record

        cls._consumer_record_no_new_env = _consumer_record_no_new_env

    @responses.activate
    def test_component_send_save_results_on_http_error(self):
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
        with mock.patch(
            "odoo.addons.webservice.models.webservice_backend."
            "WebserviceBackend._consumer_record_env",
            side_effect=self._consumer_record_no_new_env,
        ) as mo:
            with self.assertRaisesRegex(RetryableJobError, "Unauthorized"):
                self.backend._check_output_exchange_sync()
        mo.assert_called_once_with(self.record, new_cursor=True)
        self.assertTrue(self.edi_exchange_state_changed)
        self.assertEqual(
            responses.calls[0].request.headers["Content-Type"], "application/xml"
        )
        self.assertEqual(responses.calls[0].request.body, "This is a simple file")
        self.assertEqual(
            self.record._get_file_content(field_name="ws_response_content"), response
        )
