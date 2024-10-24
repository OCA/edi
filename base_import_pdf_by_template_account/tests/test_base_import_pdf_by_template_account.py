# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo.addons.base.tests.common import BaseCommon


class TestBaseImportPdfByTemplateAccount(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        generic_product = cls.env.ref(
            "base_import_pdf_by_template_account.generic_product"
        )
        cls.partner_tecnativa = cls.env.ref(
            "base_import_pdf_by_template_account.partner_tecnativa"
        )
        cls.template_invoice_tecnativa = cls.env.ref(
            "base_import_pdf_by_template_account.invoice_tecnativa"
        )
        cls.template_invoice_tecnativa.write(
            {"auto_detect_pattern": r"(?<=B 8 7 5 3 0 4 3 2)[\S\s]*"}
        )
        product_model_name = "product.product"
        cls.env.ref(
            "base_import_pdf_by_template_account.invoice_tecnativa_line_product_id"
        ).write({"default_value": f"{product_model_name},{generic_product.id}"})
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
        self.assertEqual(record.partner_id, self.partner_tecnativa)
        self.assertEqual(len(record.invoice_line_ids), 6)
        self.assertEqual(sum(record.invoice_line_ids.mapped("quantity")), 665)
        default_codes = record.invoice_line_ids.mapped("product_id.default_code")
        self.assertIn("ROTULADOR", default_codes)
        self.assertIn("BOLIGRAFO", default_codes)
        self.assertIn("LEDS", default_codes)
        self.assertIn("PLASTIFICADORA", default_codes)
        self.assertIn("LAMINAS", default_codes)
        self.assertIn("TRITURADORA", default_codes)
        self.assertIn("100.25", record.message_ids[-1].body)

    def test_account_invoice_tecnativa(self):
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        wizard = self._create_wizard_base_import_pdf_upload("account.move", attachment)
        # Similar context from Vendor invoices menu
        wizard = wizard.with_context(**{"default_move_type": "in_invoice"})
        res = wizard.action_process()
        self.assertEqual(res["res_model"], "account.move")
        record = self.env[res["res_model"]].browse(res["res_id"])
        self.assertIn(attachment, record.attachment_ids)
        self._test_account_invoice_tecnativa_data(record)

    def test_account_move_edi_decoder(self):
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        invoice = self.journal.with_context(
            default_journal_id=self.journal.id
        )._create_document_from_attachment(attachment.id)
        self.assertIn(attachment, invoice.attachment_ids)
        self._test_account_invoice_tecnativa_data(invoice)
