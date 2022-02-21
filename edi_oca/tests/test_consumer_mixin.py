# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest

from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo.tests.common import Form

from .common import EDIBackendCommonTestCase


# This clashes w/ some setup (eg: run tests w/ pytest when edi_storage is installed)
# If you still want to run `edi` tests w/ pytest when this happens, set this env var.
@unittest.skipIf(os.getenv("SKIP_EDI_CONSUMER_CASE"), "Consumer test case disabled.")
class TestConsumerMixinCase(EDIBackendCommonTestCase):
    # pylint: disable=W8110
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
        cls.exchange_type_new = cls._create_exchange_type(
            name="Test CSV output",
            code="test_csv_new_output",
            direction="output",
            exchange_file_ext="csv",
            backend_id=False,
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
            model_ids=[(4, cls.env["ir.model"]._get_id(cls.consumer_record._name))],
            enable_domain="[]",
            enable_snippet="""result = not   record._has_exchange_record(
            exchange_type.code)""",
        )
        cls.exchange_type_out.write(
            {
                "model_ids": [
                    (
                        4,
                        cls.env["ir.model"]._get_id(cls.consumer_record._name),
                    )
                ],
                "enable_domain": "[]",
                "enable_snippet": """result = not   record._has_exchange_record(
            exchange_type.code, exchange_type.backend_id)""",
            }
        )
        cls.backend_02 = cls.backend.copy()

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

    def test_expected_configuration(self):
        self.assertTrue(self.consumer_record.has_expected_edi_configuration)
        self.assertIn(
            str(self.exchange_type_out.id),
            self.consumer_record.expected_edi_configuration,
        )
        self.assertEqual(
            self.consumer_record.expected_edi_configuration[
                str(self.exchange_type_out.id)
            ],
            self.exchange_type_out.name,
        )
        action = self.consumer_record.edi_create_exchange_record(
            self.exchange_type_out.id
        )
        self.assertEqual(action["res_model"], "edi.exchange.record")
        self.consumer_record.refresh()
        self.assertNotIn(
            str(self.exchange_type_out.id),
            self.consumer_record.expected_edi_configuration,
        )
        self.assertTrue(self.consumer_record.exchange_record_ids)
        self.assertEqual(
            self.consumer_record.exchange_record_ids.type_id, self.exchange_type_out
        )

    def test_multiple_backend(self):
        self.assertIn(
            str(self.exchange_type_new.id),
            self.consumer_record.expected_edi_configuration,
        )
        action = self.consumer_record.edi_create_exchange_record(
            self.exchange_type_new.id
        )
        self.assertNotEqual(action["res_model"], "edi.exchange.record")
        self.assertEqual(action["res_model"], "edi.exchange.record.create.wiz")
        wizard = (
            self.env[action["res_model"]]
            .with_context(**action["context"])
            .create({"backend_id": self.backend_02.id})
        )
        wizard.create_edi()
        self.consumer_record.refresh()
        self.assertNotIn(
            str(self.exchange_type_new.id),
            self.consumer_record.expected_edi_configuration,
        )
        self.assertTrue(self.consumer_record.exchange_record_ids)
        self.assertEqual(
            self.consumer_record.exchange_record_ids.type_id, self.exchange_type_new
        )

    def test_form(self):
        """Testing that the form has inherited the fields and inserted them
        Unfortunately we are unable to test the buttons here
        """
        with Form(self.consumer_record) as f:
            self.assertIn("has_expected_edi_configuration", f._values)
            self.assertIn("expected_edi_configuration", f._values)
            form = etree.fromstring(f._view["arch"])
            self.assertTrue(
                form.xpath("//field[@name='has_expected_edi_configuration']")
            )
            self.assertTrue(form.xpath("//field[@name='expected_edi_configuration']"))
