# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import textwrap

import mock
from odoo_test_helper import FakeModelLoader

from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class TestConsumerAutoMixinCase(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EdiAutoExchangeConsumerTest

        cls.loader.update_registry((EdiAutoExchangeConsumerTest,))
        # ->/
        cls.model = cls.env[EdiAutoExchangeConsumerTest._name]
        cls.record = cls.model.with_context(edi__skip_auto_handle=True).create(
            {"name": "Test auto"}
        )
        cls.auto_exchange_type = cls._create_exchange_type(
            name="Test auto output",
            code="test_auto_output",
            direction="output",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.id}.test",
            model_ids=[(4, cls.env["ir.model"]._get_id(cls.model._name))],
            enable_domain="[]",
            enable_snippet="",
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_skip(self):
        with mock.patch.object(
            type(self.model), "_edi_auto_collect_todo"
        ) as mocked_collect:
            # Skip via ctx key
            record = self.model.with_context(edi__skip_auto_handle=True).create(
                {"name": "Test auto 2"}
            )
            mocked_collect.assert_not_called()
            # Skip via class attr
            with mock.patch.object(
                type(self.model),
                "_edi_no_auto_for_operation",
                new_callable=mock.PropertyMock,
            ) as mocked:
                mocked.return_value = ("create", "write")
                record = self.model.create({"name": "Test auto 2"})
                mocked_collect.assert_not_called()
                vals = {"name": "New name"}
                # Write is not allowed
                record.write(vals)
                mocked_collect.assert_not_called()
                # Allow it
                mocked.return_value = ("create",)
                record.write(vals)
                mocked_collect.assert_called_with("write", vals)

    def test_no_conf_no_trigger(self):
        with mock.patch.object(
            type(self.model), "_edi_auto_trigger_event"
        ) as mocked_trigger:
            record = self.model.create({"name": "Test auto 2"})
            mocked_trigger.assert_not_called()
            vals = {"name": "New name"}
            record.write(vals)
            mocked_trigger.assert_not_called()

    def test_no_conf_no_trigger2(self):
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_trigger_event"
            ) as mocked_trigger:
                record = self.model.create({"name": "Test auto 2"})
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"type={self.auto_exchange_type.code} "
                    f"op=%s: Auto-conf not found or disabled"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_conf_disable_no_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            """
        auto:
            disable: true
        """
        )
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_trigger_event"
            ) as mocked_trigger:
                record = self.model.create({"name": "Test auto 2"})
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"type={self.auto_exchange_type.code} "
                    f"op=%s: Auto-conf not found or disabled"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_conf_no_action_no_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            """
        auto:
            actions:
        """
        )
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_trigger_event"
            ) as mocked_trigger:
                record = self.model.create({"name": "Test auto 2"})
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"type={self.auto_exchange_type.code} "
                    f"op=%s: Auto-conf has no action configured"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    # def test_write(self):
    #     self.assertEqual(0, self.consumer_record.exchange_record_count)
    #     vals = {
    #         "model": self.consumer_record._name,
    #         "res_id": self.consumer_record.id,
    #     }
    #     exchange_type = "test_csv_output"
    #     exchange_record = self.backend.create_record(exchange_type, vals)
    #     self.consumer_record.refresh()
    #     self.assertEqual(1, self.consumer_record.exchange_record_count)
    #     action = self.consumer_record.action_view_edi_records()
    #     self.consumer_record.refresh()
    #     self.assertEqual(
    #         exchange_record, self.env["edi.exchange.record"].search(action["domain"])
    #     )
    #     self.consumer_record._has_exchange_record(exchange_type, self.backend)

    # def test_expected_configuration(self):
    #     self.assertTrue(self.consumer_record.has_expected_edi_configuration)
    #     self.assertIn(
    #         str(self.exchange_type_out.id),
    #         self.consumer_record.expected_edi_configuration,
    #     )
    #     self.assertEqual(
    #         self.consumer_record.expected_edi_configuration[
    #             str(self.exchange_type_out.id)
    #         ],
    #         {"btn": {"label": self.exchange_type_out.name}},
    #     )
    #     action = self.consumer_record.edi_create_exchange_record(
    #         self.exchange_type_out.id
    #     )
    #     self.assertEqual(action["res_model"], "edi.exchange.record")
    #     self.consumer_record.refresh()
    #     self.assertNotIn(
    #         str(self.exchange_type_out.id),
    #         self.consumer_record.expected_edi_configuration,
    #     )
    #     self.assertTrue(self.consumer_record.exchange_record_ids)
    #     self.assertEqual(
    #         self.consumer_record.exchange_record_ids.type_id, self.exchange_type_out
    #     )

    # def test_multiple_backend(self):
    #     self.assertIn(
    #         str(self.exchange_type_new.id),
    #         self.consumer_record.expected_edi_configuration,
    #     )
    #     action = self.consumer_record.edi_create_exchange_record(
    #         self.exchange_type_new.id
    #     )
    #     self.assertNotEqual(action["res_model"], "edi.exchange.record")
    #     self.assertEqual(action["res_model"], "edi.exchange.record.create.wiz")
    #     wizard = (
    #         self.env[action["res_model"]]
    #         .with_context(**action["context"])
    #         .create({"backend_id": self.backend_02.id})
    #     )
    #     wizard.create_edi()
    #     self.consumer_record.refresh()
    #     self.assertNotIn(
    #         str(self.exchange_type_new.id),
    #         self.consumer_record.expected_edi_configuration,
    #     )
    #     self.assertTrue(self.consumer_record.exchange_record_ids)
    #     self.assertEqual(
    #         self.consumer_record.exchange_record_ids.type_id, self.exchange_type_new
    #     )
