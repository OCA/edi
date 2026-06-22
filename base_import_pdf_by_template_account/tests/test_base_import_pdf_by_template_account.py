# Copyright 2024-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo import Command
from odoo.tests import new_test_user
from odoo.tests.common import users
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestBaseImportPdfByTemplateAccount(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        new_test_user(
            cls.env,
            login="test-account-user",
            groups="account.group_account_invoice,analytic.group_analytic_accounting",
        )
        cls.env.user.groups_id += cls.env.ref("analytic.group_analytic_accounting")
        # Demo data is not consistent, let's set our own template here
        # We define a different auto_detect_pattern in the existing demo template
        # to prevent it from being used.
        cls.env.ref("base_import_pdf_by_template_account.invoice_tecnativa").write(
            {"auto_detect_pattern": "custom-pattern"}
        )
        generic_product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "default_code": "GENERIC",
            }
        )
        plan = cls.env["account.analytic.plan"].create({"name": "Test plan"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Test account",
                "plan_id": plan.id,
            }
        )
        cls.partner_tecnativa = cls.env["res.partner"].create({"name": "Tecnativa"})
        cls.env["product.product"].create(
            {
                "name": "Test Rotulador",
                "default_code": "ROTULADOR",
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": cls.partner_tecnativa.id,
                            "product_code": "CONS_0001",
                        },
                    ),
                ],
            }
        )
        # We change the values of existing products so that they are not found and
        # make the test "simpler".
        cls.env.ref("base_import_pdf_by_template_account.product_boligrafo").write(
            {"seller_ids": [Command.clear()]}
        )
        cls.env.ref("base_import_pdf_by_template_account.product_leds").write(
            {"seller_ids": [Command.clear()]}
        )
        cls.env.ref("base_import_pdf_by_template_account.product_plastificadora").write(
            {"seller_ids": [Command.clear()]}
        )
        cls.env.ref("base_import_pdf_by_template_account.product_laminas").write(
            {"seller_ids": [Command.clear()]}
        )
        cls.env.ref("base_import_pdf_by_template_account.product_trituradora").write(
            {"seller_ids": [Command.clear()]}
        )
        # pylint: disable=W1401
        cls.template = cls.env[
            "base.import.pdf.template"
        ].create(
            {
                "name": "Invoices Tecnativa",
                "model_id": cls.env.ref("account.model_account_move").id,
                "child_field_id": cls.env.ref(
                    "account.field_account_move__invoice_line_ids"
                ).id,
                "auto_detect_pattern": "(B87530432)",
                "line_ids": [
                    Command.create(
                        {
                            "sequence": 10,
                            "related_model": "header",
                            "field_id": cls.env.ref(
                                "account.field_account_move__partner_id"
                            ).id,
                            "value_type": "fixed",
                            "fixed_value": f"res.partner,{cls.partner_tecnativa.id}",
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 20,
                            "related_model": "header",
                            "field_id": cls.env.ref(
                                "account.field_account_move__move_type"
                            ).id,
                            "value_type": "fixed",
                            "fixed_value_selection": cls.env.ref(
                                "account.selection__account_invoice_report__move_type__in_invoice"
                            ).id,
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 30,
                            "related_model": "lines",
                            "field_id": cls.env.ref(
                                "account.field_account_move_line__product_id"
                            ).id,
                            "pattern": r"\[([A-Z\d]+[_|-][A-Z\d]+)\]",
                            "value_type": "variable",
                            "search_field_id": cls.env.ref(
                                "product.field_product_product__seller_ids"
                            ).id,
                            "search_subfield_id": cls.env.ref(
                                "product.field_product_supplierinfo__product_code"
                            ).id,
                            "default_value": f"product.product,{generic_product.id}",
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 40,
                            "related_model": "lines",
                            "field_id": cls.env.ref(
                                "account.field_account_move_line__quantity"
                            ).id,
                            "pattern": r"\[[A-Z\d]+[_|-][A-Z\d]+\] [a-zA-Záí ]* ([0-9]{1,3})",  # noqa: E501
                            "value_type": "variable",
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 50,
                            "related_model": "lines",
                            "field_id": cls.env.ref(
                                "account.field_account_move_line__price_unit"
                            ).id,
                            "pattern": r"\[[A-Z\d]+[_|-][A-Z\d]+\] [a-zA-Záí]* [0-9]{1,3} ([0-9]{1,3}.[0-9]{2})",  # noqa: E501
                            "value_type": "variable",
                            "log_distinct_value": True,
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 60,
                            "related_model": "lines",
                            "field_id": cls.env.ref(
                                "account.field_account_move_line__analytic_distribution"
                            ).id,
                            "value_type": "fixed",
                            "fixed_value_text": (
                                f'{{"{cls.analytic_account.id}": ' "100.0}"
                            ),
                        },
                    ),
                ],
            }
        )
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )

    def _data_file(self, filename, encoding=None):
        filename = "data/" + filename
        mode = "rt" if encoding else "rb"
        with open(path.join(path.dirname(__file__), filename), mode) as file:
            data = file.read()
            return b64encode(data)

    def _create_ir_attachment(self, filename):
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": self._data_file(filename),
            }
        )

    def _create_wizard_base_import_pdf_upload(self, model, attachment):
        wizard = self.env["wizard.base.import.pdf.upload"].create(
            {
                "model": model,
                "attachment_ids": attachment.ids,
            }
        )
        return wizard

    def _test_account_invoice_tecnativa_data(self, record):
        self.assertEqual(record.move_type, "in_invoice")
        self.assertEqual(record.partner_id, self.partner_tecnativa)
        self.assertEqual(len(record.invoice_line_ids), 6)
        self.assertEqual(sum(record.invoice_line_ids.mapped("quantity")), 665)
        default_codes = record.invoice_line_ids.mapped("product_id.default_code")
        self.assertIn("ROTULADOR", default_codes)
        self.assertNotIn("BOLIGRAFO", default_codes)
        self.assertNotIn("LEDS", default_codes)
        self.assertNotIn("PLASTIFICADORA", default_codes)
        self.assertNotIn("LAMINAS", default_codes)
        self.assertNotIn("TRITURADORA", default_codes)
        self.assertIn("GENERIC", default_codes)
        self.assertIn("100.25", record.message_ids[-1].body)
        self.assertEqual(
            record.invoice_line_ids[0].analytic_distribution,
            {str(self.analytic_account.id): 100.0},
        )

    @users("test-account-user")
    def test_account_invoice_tecnativa(self):
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        wizard = self._create_wizard_base_import_pdf_upload("account.move", attachment)
        res = wizard.action_process()
        self.assertEqual(res["res_model"], "account.move")
        record = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(len(record.attachment_ids), 1)
        self.assertEqual(attachment, record.attachment_ids)
        self._test_account_invoice_tecnativa_data(record)

    def test_account_move_edi_decoder(self):
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        invoice = self.journal.with_context(
            default_journal_id=self.journal.id,
            default_move_type="in_invoice",
        )._create_document_from_attachment(attachment.id)
        self.assertEqual(len(invoice.attachment_ids), 1)
        self.assertEqual(attachment, invoice.attachment_ids)
        self._test_account_invoice_tecnativa_data(invoice)

    def test_account_move_from_alias_with_template(self):
        invoice = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create({})
        )
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        res = invoice.with_context(from_alias=True)._check_and_decode_attachment(
            attachment
        )
        self.assertEqual(res, {attachment: invoice})
        self.assertTrue(attachment.exists())
        self.assertEqual(len(invoice.attachment_ids), 1)
        self.assertEqual(attachment, invoice.attachment_ids)
        self._test_account_invoice_tecnativa_data(invoice)

    @mute_logger("odoo.models.unlink")
    def test_account_move_from_alias_without_template(self):
        invoice = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create({})
        )
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        self.template.unlink()
        res = invoice.with_context(from_alias=True)._check_and_decode_attachment(
            attachment
        )
        self.assertEqual(res, {attachment: invoice})
        self.assertTrue(attachment.exists())
        self.assertEqual(len(invoice.invoice_line_ids), 0)
