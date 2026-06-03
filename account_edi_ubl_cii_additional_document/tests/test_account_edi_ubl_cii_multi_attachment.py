# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiMultiAttachment(AccountTestInvoicingCommon):
    def _import_invoice(self):
        journal = self.company_data["default_journal_purchase"]
        file_path = (
            "account_edi_ubl_cii_additional_document/tests/"
            "test_files/bis3_bill_example.xml"
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
        bill = self._import_invoice()
        self.assertSetEqual(
            set(bill.attachment_ids.mapped("name")),
            {
                "FAC_2023_00052.csv",
                "FAC_2023_00052.png",
                "FAC_2023_00052.xlsx",
                "FAC_2023_00052.pdf",
                "test_invoice.xml",
            },
        )
        self.assertEqual(bill.message_main_attachment_id.name, "FAC_2023_00052.pdf")
