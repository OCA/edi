# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo_test_helper import FakeModelLoader
from odoo.addons.queue_job.tests.common import trap_jobs


from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import (
    FakeOutputChecker,
    FakeOutputGenerator,
    FakeOutputSender,
    FakeConfigurationListener,
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

    def test_edi_configuration(self):
        # Create new consumer record

        consumer_record = self.env["edi.exchange.consumer.test"].create(
            {"name": "Test Consumer"}
        )

        # Check configuration on create
        consumer_record.refresh()
        exchange_record = consumer_record.exchange_record_ids
        self.assertEqual(len(exchange_record), 1)
        self.assertEqual(exchange_record.type_id, self.exchange_type_out)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")


        # Check _edi_send_via_edi

        # Check generate and send output record

        # Write the existed consumer record
        consumer_record.name = "Fix Consumer"
        # check Configuration on write
        consumer_record.refresh()
        exchange_record = consumer_record.exchange_record_ids - exchange_record
        self.assertEqual(len(exchange_record), 1)
        self.assertEqual(exchange_record.type_id, self.exchange_type_out)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")
