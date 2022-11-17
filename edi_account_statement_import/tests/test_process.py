import base64
import textwrap

from unittest import mock

from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin


class TestProcessComponent(SavepointComponentCase, EDIBackendTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls._get_backend()
        cls.exc_type = cls._create_exchange_type(
            name="Import bank statement",
            code="import_bank_statement",
            direction="input",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.identifier}-{type.code}-{dt}",
            backend_id=cls.backend.id,
            advanced_settings_edit=textwrap.dedent(
                """
            components:
                process:
                    usage: input.process.account.bank.statement
            """
            ),
        )
        cls.record = cls.backend.create_record("import_bank_statement", {})
        cls.record._set_file_content(b"<fake><order></order></fake>")
        cls.wiz_model = cls.env["account.statement.import"]

    def test_lookup(self):
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._name, "edi.input.account.statement.process")

    def test_wizard_setup(self):
        comp = self.backend._get_component(self.record, "process")
        with mock.patch.object(
            type(self.wiz_model)
        ) as md_onchange:
            wiz = comp._setup_wizard()
            self.assertEqual(wiz._name, self.wiz_model._name)
            self.assertEqual(wiz.env.context["random_key"], "custom")
            self.assertEqual(
                base64.b64decode(wiz.statement_file),
            )
            self.assertEqual(wiz.statement_filename,
                             self.record.exchange_filename)
            md_onchange.assert_called()

    def test_settings(self):
        self.exc_type.advanced_settings_edit = textwrap.dedent(
            """
            components:
                process:
                    usage: input.process.account.bank.statement
            """
        )

    def test_new_statement(self):
        statement = self.env["account.bank.statement"].create(
            {
                'journal_id': 7,
                'date': self.field.Date.today(),
            }
        )
        comp = self.backend._get_component(self.record, "process")
        mock2 = mock.patch.object(type(self.wiz_model), "import_file_button")
        self.assertFalse(self.record.record)
        with mock2 as md_btn:
            md_btn.return_value = {"res_id": statement.id}
            res = comp.process()
            md_btn.assert_called()
            self.assertEqual(res, "Account statement created")
        self.assertEqual(self.record.record, statement)
