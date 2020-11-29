# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo_test_helper import FakeModelLoader

from .common import EDIBackendCommonTestCase


# This clashes w/ some setup (eg: run tests w/ pytest when edi_storage is installed)
# If you still want to run `edi` tests w/ pytest when this happens, set this env var.
@unittest.skipIf(os.getenv("SKIP_EDI_CONSUMER_CASE"), "Consumer test case disabled.")
class TestConsumerMixinCase(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EdiExchangeConsumerTest

        cls.loader.update_registry((EdiExchangeConsumerTest,))
        cls.consumer_record = cls.env["edi.exchange.consumer.test"].create(
            {"name": "Test Consumer"}
        )
        cls.exchange_type_out.exchange_filename_pattern = "{record.id}"

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_mixin(self):
        self.assertEqual(0, self.consumer_record.exchange_record_count)
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        exchange_type = "test_csv_output"
        exchange_record = self.backend.create_record(exchange_type, vals)
        self.consumer_record.refresh()
        self.assertEqual(1, self.consumer_record.exchange_record_count)
        action = self.consumer_record.action_view_edi_records()
        self.consumer_record.refresh()
        self.assertEqual(
            exchange_record, self.env["edi.exchange.record"].search(action["domain"])
        )
        self.consumer_record._has_exchange_record(exchange_type, self.backend)
