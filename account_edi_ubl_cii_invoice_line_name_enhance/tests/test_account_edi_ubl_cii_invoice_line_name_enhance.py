# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiInvoiceLineNameEnhance(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()

    def _import_invoice(self, journal, file_path=None):
        if file_path is None:
            file_path = (
                "account_edi_ubl_cii_invoice_line_name_enhance/tests/test_files/"
                "bis3_bill_example.xml"
            )
        with file_open(file_path, "rb") as file:
            xml_attachment = self.env["ir.attachment"].create(
                {
                    "mimetype": "application/xml",
                    "name": "test_invoice.xml",
                    "raw": file.read(),
                }
            )
        move = (
            self.env["account.journal"]
            .with_context(default_journal_id=journal.id)
            ._create_document_from_attachment(xml_attachment.id)
        )
        return move

    def test_0(self):
        """
        description and name are different
        invoice line name = product name + description
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.name, "Locations and leasing\ndiscount 10%")

    def test_1(self):
        """
        name in description
        invoice line name = description
        """
        file_path = (
            "account_edi_ubl_cii_invoice_line_name_enhance/tests/test_files/"
            "bis3_bill_example_name_same_description.xml"
        )
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], file_path=file_path
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.name, "Locations and leasing with discount 10%")
