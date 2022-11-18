# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# @author: Lois Rilo <lois.rilo@forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import textwrap

import mock

from odoo import exceptions

from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin


class TestProcessComponent(SavepointComponentCase, EDIBackendTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls._get_backend()
        cls.exc_type = cls._create_exchange_type(
            name="Test SO import",
            code="test_so_import",
            direction="input",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.identifier}-{type.code}-{dt}",
            backend_id=cls.backend.id,
            advanced_settings_edit=textwrap.dedent(
                """
            components:
                process:
                    usage: input.process.account.invoice
            account_invoice_import:
                wiz_ctx:
                    random_key: custom
            """
            ),
        )
        cls.record = cls.backend.create_record("test_so_import", {})
        cls.record._set_file_content(b"<fake><invoice></invoice></fake>")
        cls.wiz_model = cls.env["account.invoice.import"]

    def test_lookup(self):
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._name, "edi.input.account.invoice.process")

    def test_wizard_setup(self):
        comp = self.backend._get_component(self.record, "process")
        wiz = comp._setup_wizard()
        self.assertEqual(wiz._name, self.wiz_model._name)
        self.assertEqual(wiz.env.context["random_key"], "custom")
        self.assertEqual(
            base64.b64decode(wiz.invoice_file), b"<fake><invoice></invoice></fake>"
        )
        self.assertEqual(wiz.invoice_filename, self.record.exchange_filename)

    def test_settings(self):
        self.exc_type.advanced_settings_edit = textwrap.dedent(
            """
            components:
                process:
                    usage: input.process.account.invoice
            account_invoice_import:
                post_invoice: true
            """
        )
        comp = self.backend._get_component(self.record, "process")
        self.assertTrue(comp._invoice_should_be_posted())

    def test_existing_invoice(self):
        invoice = self.env["account.move"].create(
            {"partner_id": self.env["res.partner"].search([], limit=1).id}
        )
        comp = self.backend._get_component(self.record, "process")
        m1 = mock.patch.object(type(self.wiz_model), "import_invoice")
        m2 = mock.patch.object(
            type(self.wiz_model),
            "invoice_id",
            new_callable=mock.PropertyMock,
        )
        m3 = mock.patch.object(
            type(self.wiz_model),
            "state",
            new_callable=mock.PropertyMock,
        )
        rec_msgs = self.record.message_ids
        # Simulate the wizard detected an existing invoice state
        with m1 as md_btn, m2 as md_inv_id, m3 as md_state:
            md_inv_id.return_value = invoice
            md_state.return_value = "update"
            with self.assertRaisesRegex(
                exceptions.UserError, "Invoice has already been imported before"
            ):
                comp.process()
                md_btn.assert_called()
        new_msg = self.record.message_ids - rec_msgs
        self.assertIn("Invoice has already been imported before", new_msg.body)
        self.assertIn(
            f"/web#id={invoice.id}&amp;model=account.move&amp;view_type=form",
            new_msg.body,
        )

    def test_new_invoice(self):
        invoice = self.env["account.move"].create(
            {"partner_id": self.env["res.partner"].search([], limit=1).id}
        )
        comp = self.backend._get_component(self.record, "process")
        mock_1 = mock.patch.object(type(self.wiz_model), "import_invoice")
        self.assertFalse(self.record.record)
        # Simulate the wizard detected an existing invoice state
        with mock_1 as md_btn:
            md_btn.return_value = {"res_id": invoice.id}
            res = comp.process()
            md_btn.assert_called()
            self.assertEqual(res, f"Invoice {invoice.name} created")

        self.assertEqual(self.record.record, invoice)
