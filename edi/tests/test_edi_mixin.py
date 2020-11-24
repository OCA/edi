# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from .common import EDIBackendCommonTestCase


class EDIBackendTestCase(EDIBackendCommonTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import EdiExchangeConsumerTest

        cls.loader.update_registry((EdiExchangeConsumerTest,))
        cls.new_record = (
            cls.env["edi.exchange.consumer.test"]
            .with_context(test_backend_id=cls.backend.id)
            .create({})
        )
        cls.exchange_type_out.exchange_filename_pattern = "{record.id}"

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def setUp(self):
        super().setUp()

    def test_mixin(self):
        self.assertEqual(0, self.new_record.exchange_record_count)
        vals = {
            "model": self.new_record._name,
            "res_id": self.new_record.id,
        }
        exchange_type = "test_csv_output"
        exchange_record = self.backend.create_record(exchange_type, vals)
        self.new_record.refresh()
        self.assertEqual(1, self.new_record.exchange_record_count)
        action = self.new_record.action_view_edi_records()
        self.new_record.refresh()
        self.assertEqual(
            exchange_record, self.env["edi.exchange.record"].search(action["domain"])
        )
        self.new_record._has_exchange_record(exchange_type, self.backend)
