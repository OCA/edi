# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo.addons.base.tests.common import BaseCommon


class TestBaseImportPdfByTemplate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_decathlon = cls.env.ref(
            "test_base_import_pdf_by_template.partner_decathlon"
        )
        cls.template_po_decathlon = cls.env.ref(
            "test_base_import_pdf_by_template.po_decathlon"
        )
        cls.partner_tecnativa = cls.env.ref(
            "test_base_import_pdf_by_template.partner_tecnativa"
        )
        cls.template_invoice_tecnativa = cls.env.ref(
            "test_base_import_pdf_by_template.invoice_tecnativa"
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

    def _get_attachments(self, record):
        return self.env["ir.attachment"].search(
            [("res_model", "=", record._name), ("res_id", "=", record.id)]
        )

    def test_purchase_order_decathlon(self):
        attachment = self._create_ir_attachment("purchase_order_declathon.pdf")
        wizard = self._create_wizard_base_import_pdf_upload(
            "purchase.order", attachment
        )
        res = wizard.action_process()
        self.assertEqual(res["res_model"], "purchase.order")
        record = self.env[res["res_model"]].browse(res["res_id"])
        attachments = self._get_attachments(record)
        self.assertEqual(record.partner_id, self.partner_decathlon)
        self.assertEqual(record.partner_ref, "ES9812110233")
        self.assertEqual(record.origin, "fixed-origin")
        self.assertIn(attachment, attachments)
        self.assertEqual(len(record.order_line), 5)
        self.assertEqual(sum(record.order_line.mapped("product_uom_qty")), 5)
        default_codes = record.order_line.mapped("product_id.default_code")
        self.assertIn("MOCHILA", default_codes)
        self.assertIn("AISLANTE", default_codes)
        self.assertIn("HAMACA", default_codes)
        self.assertIn("BOTIQUIN", default_codes)
        self.assertIn("GENERIC", default_codes)
        self.assertIn("66.11", record.message_ids.body)

    def test_account_invoice_tecnativa(self):
        attachment = self._create_ir_attachment("account_invoice_tecnativa.pdf")
        wizard = self._create_wizard_base_import_pdf_upload("account.move", attachment)
        # Similar context from Customer invoices menu
        wizard = wizard.with_context(**{"default_move_type": "out_invoice"})
        res = wizard.action_process()
        self.assertEqual(res["res_model"], "account.move")
        record = self.env[res["res_model"]].browse(res["res_id"])
        attachments = self._get_attachments(record)
        self.assertEqual(record.move_type, "in_invoice")
        self.assertEqual(record.partner_id, self.partner_tecnativa)
        self.assertIn(attachment, attachments)
        self.assertEqual(len(record.invoice_line_ids), 6)
        self.assertEqual(sum(record.invoice_line_ids.mapped("quantity")), 665)
        default_codes = record.invoice_line_ids.mapped("product_id.default_code")
        self.assertIn("ROTULADOR", default_codes)
        self.assertIn("BOLIGRAFO", default_codes)
        self.assertIn("LEDS", default_codes)
        self.assertIn("PLASTIFICADORA", default_codes)
        self.assertIn("LAMINAS", default_codes)
        self.assertIn("TRITURADORA", default_codes)
        self.assertIn("100.25", record.message_ids.body)
