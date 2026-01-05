# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

ACC_NUMBER = "LU071241358706500000"


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiRetrieveArchivedPartnerBank(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "ALD Automotive LU", "vat": "LU25587702"}
        )

    def _import_invoice(self, journal, file_path=None):
        if file_path is None:
            file_path = (
                "account_edi_ubl_cii_retrieve_archived_partner_bank/tests/test_files/"
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
        Default behavior
        the bank account is created if not found
        """
        self.assertFalse(self.partner.bank_ids)
        self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertTrue(self.partner.bank_ids)
        self.assertEqual(self.partner.bank_ids.acc_number, ACC_NUMBER)

    def test_1(self):
        """
        Existing active bank account:
        if a matching active partner bank account already exists, the import
        must reuse it and not create a duplicate
        """
        bank_account = self.env["res.partner.bank"].create(
            {
                "acc_number": ACC_NUMBER,
                "partner_id": self.partner.id,
                "allow_out_payment": True,
                "active": True,
            }
        )
        self.assertEqual(len(self.partner.bank_ids), 1)
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertEqual(bill.partner_id.bank_ids, bank_account)

    def test_2(self):
        """
        Archived bank account:
        if a matching partner bank account exists but is archived, the import
        must retrieve it instead of attempting to create a new one (which would
        fail due to the SQL uniqueness constraint)

        the archived bank account is automatically reactivated
        """
        bank_account = self.env["res.partner.bank"].create(
            {
                "acc_number": ACC_NUMBER,
                "partner_id": self.partner.id,
                "allow_out_payment": True,
                "active": False,
            }
        )
        self.assertEqual(len(self.partner.with_context(active_test=False).bank_ids), 1)
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertEqual(bill.partner_id.bank_ids, bank_account)
        self.assertTrue(bank_account.active)
