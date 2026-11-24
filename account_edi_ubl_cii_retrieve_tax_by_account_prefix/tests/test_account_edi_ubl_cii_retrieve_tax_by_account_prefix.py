# Copyright 2026 ACSONE SA/NV,BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

TEST_FILES_DIR = "account_edi_ubl_cii_retrieve_tax_by_account_prefix/tests/test_files"


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiRetrieveTaxByAccountPrefix(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()

        cls.account_expense_61 = cls.env["account.account"].create(
            {
                "name": "Expense 61",
                "code": "611000X",
                "account_type": "expense",
            }
        )
        cls.account_expense_62 = cls.env["account.account"].create(
            {
                "name": "Expense 62",
                "code": "621000X",
                "account_type": "expense",
            }
        )
        cls.account_expense_63 = cls.env["account.account"].create(
            {
                "name": "Expense 63",
                "code": "631000X",
                "account_type": "expense",
            }
        )

        cls.product_leasing = cls.env["product.product"].create(
            {
                "name": "Leasing product",
                "default_code": "leasing001",
                "detailed_type": "service",
                "purchase_ok": True,
                "property_account_expense_id": cls.account_expense_61.id,
            }
        )

        cls.tax_33_no_code = cls.env["account.tax"].create(
            {
                "name": "33% no code",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 33,
                "sequence": 10,
            }
        )
        cls.tax_33_code_s = cls.env["account.tax"].create(
            {
                "name": "33% S",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 33,
                "sequence": 100,
                "ubl_cii_tax_category_code": "S",
            }
        )
        cls.tax_33_code_s_prefix_61 = cls.env["account.tax"].create(
            {
                "name": "33% S 61",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 33,
                "sequence": 110,
                "ubl_cii_tax_category_code": "S",
                "allowed_account_prefix": "61",
            }
        )
        cls.tax_33_code_k_no_reason = cls.env["account.tax"].create(
            {
                "name": "33% K no reason",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 33,
                "sequence": 130,
                "ubl_cii_tax_category_code": "K",
            }
        )
        cls.tax_33_code_k = cls.env["account.tax"].create(
            {
                "name": "33% K VATEX_EU_IC",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 33,
                "sequence": 140,
                "ubl_cii_tax_category_code": "K",
                "ubl_cii_tax_exemption_reason_code": "VATEX_EU_IC",
            }
        )

    def _set_product_expense_account(self, account):
        self.product_leasing.property_account_expense_id = account

    def _import_invoice(self, journal, file_name=None):
        if not file_name:
            file_name = "bis3_bill_example.xml"
        file_path = f"{TEST_FILES_DIR}/{file_name}"
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
        default behavior:
        if no ubl_cii_tax_category_code, take the first tax that matches amount and type
        """
        (
            self.tax_33_code_s + self.tax_33_code_s_prefix_61
        ).ubl_cii_tax_category_code = False

        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.tax_ids, self.tax_33_no_code)

    def test_1(self):
        """
        match tax by UNECE category code
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.tax_ids, self.tax_33_code_s_prefix_61)

    def test_2(self):
        """
        no UNECE code in the file
        """
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], "bis3_bill_no_code.xml"
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.tax_ids, self.tax_33_no_code)

    def test_3(self):
        """
        no change in sale behavior
        """
        bill = self._import_invoice(
            self.company_data["default_journal_sale"], "bis3_bill_example.xml"
        )
        inv_line = bill.invoice_line_ids
        self.assertNotEqual(inv_line.tax_ids, self.tax_33_no_code)

    def test_4(self):
        """
        default behavior if tax type is not VAT
        """
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], "bis3_bill_not_vat.xml"
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.tax_ids, self.tax_33_no_code)

    def test_5(self):
        """
        import with exemption reason
        """
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"],
            "bis3_bill_k_vatex_eu_ic.xml",
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.tax_ids, self.tax_33_code_k)
        self.assertEqual(
            inv_line.tax_ids.ubl_cii_tax_exemption_reason_code, "VATEX_EU_IC"
        )

    def test_6(self):
        """
        when the imported product uses an expense account starting with 60,
        the importer should select the tax restricted to prefix 60
        """
        self._set_product_expense_account(self.account_expense_61)
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.product_id, self.product_leasing)
        self.assertEqual(inv_line.account_id, self.account_expense_61)
        self.assertEqual(inv_line.tax_ids, self.tax_33_code_s_prefix_61)

    def test_7(self):
        """
        when the imported product uses an expense account starting with 61,
        the importer should select the tax restricted to prefix 61
        """
        self._set_product_expense_account(self.account_expense_61)
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.product_id, self.product_leasing)
        self.assertEqual(inv_line.account_id, self.account_expense_61)
        self.assertEqual(inv_line.tax_ids, self.tax_33_code_s_prefix_61)

    def test_8(self):
        """
        if no restricted tax matches the line account prefix,
        keep the default tax selected by the standard logic
        """
        self._set_product_expense_account(self.account_expense_62)
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.product_id, self.product_leasing)
        self.assertEqual(inv_line.account_id, self.account_expense_62)
        self.assertEqual(inv_line.tax_ids, self.tax_33_code_s)
