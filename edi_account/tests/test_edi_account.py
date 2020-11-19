# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account.tests.account_test_savepoint import AccountTestInvoicingCommon


@tagged("-at_install", "post_install")
class TestEdi(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.invoice = cls.init_invoice("out_invoice")
        cls.format = cls.env.ref("edi_account.edi_format_mail")
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

    def test_edi_journal(self):
        self.invoice.post()
        self.assertEqual("posted", self.invoice.state)
        self.assertFalse(self.invoice.missing_edi_documents)
        self.invoice.journal_id.account_move_edi_format_ids = self.format
        self.invoice.refresh()
        self.assertTrue(self.invoice.missing_edi_documents)
        self.assertEqual(0, self.invoice.edi_document_count)
        self.invoice.generate_missing_edi_documents()
        self.invoice.refresh()
        self.assertFalse(self.invoice.missing_edi_documents)
        self.assertEqual(1, self.invoice.edi_document_count)
        document = self.invoice.edi_document_ids
        self.assertEqual(1, len(document.message_ids))
        document.action_send()
        self.assertEqual(3, len(document.message_ids))

    def test_edi_partner(self):
        self.invoice.post()
        self.assertEqual("posted", self.invoice.state)
        self.assertFalse(self.invoice.missing_edi_documents)
        self.invoice.partner_id.account_move_edi_format_ids = self.format
        self.invoice.refresh()
        self.assertTrue(self.invoice.missing_edi_documents)
        self.assertEqual(0, self.invoice.edi_document_count)
        self.invoice.generate_missing_edi_documents()
        self.invoice.refresh()
        self.assertFalse(self.invoice.missing_edi_documents)
        self.assertEqual(1, self.invoice.edi_document_count)
        document = self.invoice.edi_document_ids
        self.assertEqual(1, len(document.message_ids))
        document.action_send()
        self.assertEqual(3, len(document.message_ids))
