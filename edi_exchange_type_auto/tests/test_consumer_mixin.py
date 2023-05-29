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
        cls.partner1 = cls.env["res.partner"].create({"name": "Avg Customer 1"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Avg Customer 2"})

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
                mocked_collect.assert_called_with("write", [vals])

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
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Auto-conf not found or disabled"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_conf_disable_no_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
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
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Auto-conf not found or disabled"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_edi_disable_flag_no_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
                when:
                    - write
        """
        )
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_trigger_event"
            ) as mocked_trigger:
                record = self.model.create(
                    {"name": "Test auto 2", "disable_edi_auto": True}
                )
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"op=%s: EDI auto disabled for rec={record.id}"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_conf_no_action_no_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
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
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Auto-conf has no action configured"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_trigger.assert_not_called()
                vals = {"name": "New name"}
                record.write(vals)
                self.assertEqual(watcher.output[1], expected_msg % "write")
                mocked_trigger.assert_not_called()

    def test_conf_when_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
                actions:
                    generate:
                        when:
                            - create
                        trigger_fields:
                            - name
        """
        )
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_handle"
            ) as mocked_handler:
                record = self.model.create({"name": "Test auto 2"})
                mocked_handler.assert_called()
                mocked_handler.reset_mock()
                vals = {"name": "New name"}
                record.write(vals)
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Operation not allowed for action=generate"
                )
                self.assertEqual(watcher.output[0], expected_msg % "write")
                mocked_handler.assert_not_called()

    def test_conf_if_trigger(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
                actions:
                    generate:
                        when:
                            - create
                        trigger_fields:
                            - name
                        if:
                            callable: _edi_test_check_generate
        """
        )
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_handle"
            ) as mocked_handler:
                record = self.model.with_context(
                    _edi_test_check_generate_pass=True
                ).create({"name": "Test auto 2"})
                info = record._edi_test_check_generate_called_with.pop()
                self.assertEqual(
                    info.as_dict(),
                    {
                        "edi_type_id": self.auto_exchange_type.id,
                        "edi_action": "generate",
                        "conf": {
                            "when": ["create"],
                            "trigger_fields": ["name"],
                            "if": {"callable": "_edi_test_check_generate"},
                        },
                        "triggered_by": "name",
                        "_records": {
                            "source": {
                                "model": "edi.auto.exchange.consumer.test",
                                "id": record.id,
                            },
                            "target": {
                                "model": "edi.auto.exchange.consumer.test",
                                "id": record.id,
                            },
                        },
                        "vals": {"name": "Test auto 2"},
                        "old_vals": {"name": "Test auto 2"},
                        "force": False,
                        "event_only": False,
                    },
                )
                mocked_handler.assert_called()
                mocked_handler.reset_mock()
                record = self.model.with_context(
                    _edi_test_check_generate_pass=False
                ).create({"name": "Test auto 3"})
                mocked_handler.assert_not_called()
                info = record._edi_test_check_generate_called_with.pop()
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Checker _edi_test_check_generate skip action"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")

    def test_conf_skip_partner(self):
        self.auto_exchange_type.advanced_settings_edit = textwrap.dedent(
            f"""
        auto:
            '{self.model._name}':
                actions:
                    generate:
                        when:
                            - create
                        trigger_fields:
                            - name
        """
        )
        self.auto_exchange_type.partner_ids += self.partner2
        with self.assertLogs("edi_exchange_auto", level="DEBUG") as watcher:
            with mock.patch.object(
                type(self.model), "_edi_auto_handle"
            ) as mocked_handler:
                record = self.model.create(
                    {"name": "Test auto 2", "partner_id": self.partner1.id}
                )
                expected_msg = (
                    f"DEBUG:edi_exchange_auto:"
                    f"Skip model={self.model._name} "
                    f"op=%s "
                    f"type={self.auto_exchange_type.code}: "
                    f"Exchange not enabled for partner on rec={record.id}"
                )
                self.assertEqual(watcher.output[0], expected_msg % "create")
                mocked_handler.assert_not_called()
                mocked_handler.reset_mock()
                self.model.create(
                    {"name": "Test auto 3", "partner_id": self.partner2.id}
                )
                mocked_handler.assert_called()
