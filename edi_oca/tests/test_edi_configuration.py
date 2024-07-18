# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo_test_helper import FakeModelLoader

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import (
    FakeConfigurationListener,
    FakeOutputChecker,
    FakeOutputGenerator,
    FakeOutputSender,
)


# This clashes w/ some setup (eg: run tests w/ pytest when edi_storage is installed)
# If you still want to run `edi` tests w/ pytest when this happens, set this env var.
@unittest.skipIf(os.getenv("SKIP_EDI_CONSUMER_CASE"), "Consumer test case disabled.")
class TestEDIConfigurations(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls,
            FakeOutputGenerator,
            FakeOutputSender,
            FakeOutputChecker,
            FakeConfigurationListener,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()
        FakeOutputSender.reset_faked()
        FakeOutputChecker.reset_faked()
        self.consumer_record = self.env["edi.exchange.consumer.test"].create(
            {
                "name": "Test Consumer",
                "edi_config_ids": [
                    (4, self.create_config.id),
                    (4, self.write_config.id),
                ],
            }
        )

    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EdiExchangeConsumerTest

        cls.loader.update_registry((EdiExchangeConsumerTest,))
        cls.exchange_type_out.exchange_filename_pattern = "{record.id}"
        cls.edi_configuration = cls.env["edi.configuration"]
        cls.create_config = cls.edi_configuration.create(
            {
                "name": "Create Config",
                "active": True,
                "code": "create_config",
                "backend_id": cls.backend.id,
                "type_id": cls.exchange_type_out.id,
                "trigger": "on_record_create",
                "model": cls.env["ir.model"]._get_id("edi.exchange.consumer.test"),
                "snippet_do": "record._edi_send_via_edi(conf.type_id)",
            }
        )
        cls.write_config = cls.edi_configuration.create(
            {
                "name": "Write Config 1",
                "active": True,
                "code": "write_config",
                "backend_id": cls.backend.id,
                "type_id": cls.exchange_type_out.id,
                "trigger": "on_record_write",
                "model": cls.env["ir.model"]._get_id("edi.exchange.consumer.test"),
                "snippet_do": "record._edi_send_via_edi(conf.type_id)",
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_edi_send_via_edi_config(self):
        # Check configuration on create
        self.consumer_record.refresh()
        exchange_record = self.consumer_record.exchange_record_ids
        self.assertEqual(len(exchange_record), 1)
        self.assertEqual(exchange_record.type_id, self.exchange_type_out)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")
        # Write the existed consumer record
        self.consumer_record.name = "Fixed Consumer"
        # check Configuration on write
        self.consumer_record.refresh()
        exchange_record = self.consumer_record.exchange_record_ids - exchange_record
        self.assertEqual(len(exchange_record), 1)
        self.assertEqual(exchange_record.type_id, self.exchange_type_out)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")

    def test_edi_code_snippet(self):
        expected_value = {
            "todo": True,
            "snippet_do_vars": {
                "a": 1,
                "b": 2,
            },
            "event_only": True,
            "tracked_fields": ["state"],
            "edi_action": "new_action",
        }
        # Simulate the snippet_before_do
        self.write_config.snippet_before_do = "result = " + str(expected_value)
        # Execute with the raw data
        vals = self.write_config.edi_exec_snippet_before_do(
            self.consumer_record,
            tracked_fields=[],
            edi_action="generate",
        )
        # Check the new vals after execution
        self.assertEqual(vals, expected_value)

        # Check the snippet_do
        expected_value = {
            "change_state": True,
            "snippet_do_vars": {
                "a": 1,
                "b": 2,
            },
            "record": self.consumer_record,
            "tracked_fields": ["state"],
        }
        snippet_do = """\n
old_state = old_value.get("state", False)\n
new_state = vals.get("state", False)\n
result = {\n
    "change_state": True if old_state and new_state and old_state != new_state else False,\n
    "snippet_do_vars": snippet_do_vars,\n
    "record": record,\n
    "tracked_fields": tracked_fields,\n
}
        """
        self.write_config.snippet_do = snippet_do
        # Execute with the raw data
        record_id = self.consumer_record.id
        vals = self.write_config.edi_exec_snippet_do(
            self.consumer_record,
            tracked_fields=[],
            edi_action="generate",
            old_vals={record_id: dict(state="draft")},
            vals={record_id: dict(state="confirmed")},
        )
        # Check the new vals after execution
        self.assertEqual(vals, expected_value)
