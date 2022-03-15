# Copyright 2022 Téo Goddet
# @author: Téo Goddet <teo.goddet@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import textwrap

import mock

from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin


class TestProcessComponent(SavepointComponentCase, EDIBackendTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls._get_backend()
        cls.exc_type = cls._create_exchange_type(
            name="Test bank statement import",
            code="test_bank_statement_import",
            direction="input",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.identifier}-{type.code}-{dt}",
            backend_id=cls.backend.id,
            advanced_settings_edit=textwrap.dedent(
                """
            components:
                process:
                    usage: input.process.bank.statement
            bank_statement:
                wiz_ctx:
                    random_key: custom
            """
            ),
        )
        cls.record = cls.backend.create_record("test_bank_statement_import", {})
        cls.record._set_file_content(b"<fake><statement></statement></fake>")
        cls.wiz_model = cls.env["account.statement.import"]

    def test_lookup(self):
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._name, "edi.input.bank.statement.process")

    def test_wizard_setup(self):
        comp = self.backend._get_component(self.record, "process")
        wiz = comp._setup_wizard()

        self.assertEqual(wiz._name, self.wiz_model._name)
        self.assertEqual(wiz.env.context["random_key"], "custom")
        self.assertEqual(
            base64.b64decode(wiz.statement_file),
            b"<fake><statement></statement></fake>",
        )
        self.assertEqual(wiz.statement_filename, self.record.exchange_filename)

    def test_wizard_process(self):
        comp = self.backend._get_component(self.record, "process")
        mock1 = mock.patch.object(type(self.wiz_model), "import_single_file")
        mock2 = mock.patch.object(type(comp), "_handle_result")
        with mock1 as md_import_single_file, mock2 as md_handle_result:
            comp.process()
            md_import_single_file.assert_called()
            md_handle_result.assert_called()

    def test_no_statement(self):
        comp = self.backend._get_component(self.record, "process")
        result = comp._handle_result([], self.record.exchange_filename)

        self.assertEqual(comp.exchange_record.res_id, False)
        self.assertEqual(comp.exchange_record.model, False)
        self.assertEqual(result, True)

    def test_single_statement_result_and_auto_post(self):
        statement = self.env["account.bank.statement"].create(
            {
                "name": "Test Statement",
                "journal_id": self.env["account.journal"]
                .search(
                    [
                        ("company_id", "=", self.env.user.company_id.id),
                        ("type", "=", "bank"),
                    ],
                    limit=1,
                )
                .id,
            }
        )

        self.record.type_id.advanced_settings_edit = textwrap.dedent(
            """
            components:
                process:
                    usage: input.process.bank.statement
            bank_statement:
                auto_post: true
            """
        )

        comp = self.backend._get_component(self.record, "process")
        comp._handle_result([statement.id], self.record.exchange_filename)

        self.assertEqual(comp.exchange_record.res_id, statement.id)
        self.assertEqual(comp.exchange_record.model, "account.bank.statement")
        self.assertEqual(statement.state, "posted")

    def test_multiple_statement_result_and_no_auto_post(self):
        statement1 = self.env["account.bank.statement"].create(
            {
                "name": "Test Statement 1",
                "journal_id": self.env["account.journal"]
                .search(
                    [
                        ("company_id", "=", self.env.user.company_id.id),
                        ("type", "=", "bank"),
                    ],
                    limit=1,
                )
                .id,
            }
        )
        statement2 = self.env["account.bank.statement"].create(
            {
                "name": "Test Statement 2",
                "journal_id": self.env["account.journal"]
                .search(
                    [
                        ("company_id", "=", self.env.user.company_id.id),
                        ("type", "=", "bank"),
                    ],
                    limit=1,
                )
                .id,
            }
        )

        comp = self.backend._get_component(self.record, "process")
        comp._handle_result(
            [statement1.id, statement2.id], self.record.exchange_filename
        )

        self.assertEqual(len(comp.exchange_record.related_exchange_ids), 2)
        for child_exch in comp.exchange_record.related_exchange_ids:
            self.assertIn(child_exch.res_id, [statement1.id, statement2.id])
            self.assertEqual(child_exch.model, "account.bank.statement")

        self.assertEqual(statement1.state, "open")
        self.assertEqual(statement2.state, "open")
