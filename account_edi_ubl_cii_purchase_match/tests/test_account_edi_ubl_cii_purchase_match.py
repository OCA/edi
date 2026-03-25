# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiPurchaseMatch(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()
        cls.env["ir.sequence"].search(
            [("code", "=", "purchase.order")], limit=1
        ).prefix = "PO"
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "standard_price": 100}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "ALD Automotive LU", "vat": "LU25587702"}
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "name": "PO0032",
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_qty": 1,
                            "price_unit": 657,
                        }
                    ),
                ],
            }
        )
        cls.po_line = cls.purchase_order.order_line
        cls.purchase_order.button_confirm()

    def _import_invoice(self, journal, file_path=None):
        if file_path is None:
            file_path = (
                "account_edi_ubl_cii_purchase_match/tests/test_files/"
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

    def _create_purchase_order(self, product, name=None):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 1000,
                        }
                    ),
                ],
            }
        )
        if name:
            po.name = name
        po.button_confirm()
        return po

    def test_0(self):
        """
        Default behavior
        without matching criteria, no purchase line or product
        is assigned. Sale journals are also ignored
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertEqual(bill.partner_id, self.partner)
        inv_line = bill.invoice_line_ids
        self.assertFalse(inv_line.purchase_line_id)
        self.assertFalse(inv_line.product_id)
        invoice = self._import_invoice(self.company_data["default_journal_sale"])
        self.assertEqual(invoice.partner_id, self.partner)
        inv_line = invoice.invoice_line_ids
        self.assertFalse(inv_line.purchase_line_id)
        self.assertFalse(inv_line.product_id)

    def test_1(self):
        """
        OrderReference matches a purchase order, but no product match is found.
        Standard behavior is disabled: no PO lines are created from the PO, only the
        UBL invoice line is imported
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(len(inv_line), 1)  # standard behavior is desabled
        self.assertFalse(inv_line.purchase_line_id)
        self.assertFalse(inv_line.product_id)

    def test_2(self):
        """
        The product name matches the UBL line description, so the vendor bill line is
        linked to the PO line and the product is set accordingly
        """
        self.product.name = "Locations and leasing"
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)
        return inv_line

    def test_3(self):
        """
        The supplier product name (defined on the product variant via supplierinfo)
        matches the UBL line description, so the bill line is correctly linked to the
        PO line and product
        """

        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_name": "Locations and leasing",
                "product_id": self.product.id,
            }
        )
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)

    def test_4(self):
        """
        The supplier product name (defined on the product template via supplierinfo)
        matches the UBL line description, so the bill line is linked to the PO line and
        product
        """

        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_name": "Locations and leasing",
                "product_tmpl_id": self.product.product_tmpl_id.id,
            }
        )
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)

    def test_5(self):
        """
        When no product match is found, the user manually links the bill line to the PO
        line, the supplier info is updated with the product supplier name
        On the next import, the supplierinfo is used to automatically match the
        bill line with the correct PO line
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertFalse(inv_line.purchase_line_id)
        self.assertEqual(inv_line.price_unit, 657.0)
        action = inv_line.action_select_purchase_line()
        wizard = (
            self.env[action.get("res_model")]
            .with_context(**action.get("context"))
            .create({})
        )
        self.assertEqual(wizard.move_line_id, inv_line)
        self.assertEqual(wizard.purchase_order_ids, self.purchase_order)
        wizard.product_id = self.product
        wizard.select_purchase_line()
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        bill.unlink()
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)

    def test_6(self):
        """
        price unit imported from file is unchanged after po auto match
        """
        inv_line = self.test_2()
        self.assertEqual(inv_line.price_unit, 657.0)
        inv_line.product_id = False
        inv_line.product_id = self.product
        self.assertEqual(inv_line.price_unit, 100)

    def test_7(self):
        """
        price unit imported from file is unchanged after po manual match
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.price_unit, 657.0)
        action = inv_line.action_select_purchase_line()
        wizard = (
            self.env[action.get("res_model")]
            .with_context(**action.get("context"))
            .create({})
        )
        wizard.product_id = self.product
        wizard.select_purchase_line()
        self.assertEqual(inv_line.price_unit, 657.0)

    def test_8(self):
        """match product by default_code"""
        self.product.default_code = "leasing001"
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)

    def test_9(self):
        """match product by supplier code"""
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_code": "leasing001",
                "product_id": self.product.id,
            }
        )
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)

    def test_10(self):
        """match product by supplier code for product template suuplierinfo"""
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_code": "leasing001",
                "product_tmpl_id": self.product.product_tmpl_id.id,
            }
        )
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.purchase_line_id, self.po_line)
        self.assertEqual(inv_line.product_id, self.product)

    def test_11(self):
        """
        product supplier code is stored in seller information at manual match
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.supplier_product_code, "leasing001")
        self.assertEqual(inv_line.price_unit, 657.0)
        action = inv_line.action_select_purchase_line()
        wizard = (
            self.env[action.get("res_model")]
            .with_context(**action.get("context"))
            .create({})
        )
        wizard.product_id = self.product
        wizard.select_purchase_line()
        self.assertEqual(self.product.seller_ids.product_code, "leasing001")

    def test_12(self):
        """test purchase price unit mismatch warning"""
        self.product.default_code = "leasing001"
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"],
            file_path="account_edi_ubl_cii_purchase_match/tests/test_files/"
            "bis3_bill_example_price_unit_mismatch.xml",
        )
        self.assertTrue(bill.purchase_mismatch)
        self.assertIn(
            "Unit price differs from the purchase order line",
            bill.purchase_mismatch_details,
        )
        bill.action_post()
        self.assertFalse(bill.purchase_mismatch)
        self.assertFalse(bill.purchase_mismatch_details)

    def test_13(self):
        """test purchase invoiced qty mismatch warning"""
        self.product.default_code = "leasing001"
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"],
            file_path="account_edi_ubl_cii_purchase_match/tests/test_files/"
            "bis3_bill_example_invoiced_qty_mismatch.xml",
        )
        self.assertTrue(bill.purchase_mismatch)
        self.assertIn(
            "Invoiced quantity exceeds the ordered quantity",
            bill.purchase_mismatch_details,
        )
        bill.action_post()
        self.assertFalse(bill.purchase_mismatch)
        self.assertFalse(bill.purchase_mismatch_details)

    def _extract_refs(self, invoice_origin):
        return self.env["account.move"]._extract_purchase_references_from_origin(
            invoice_origin
        )

    def test_14(self):
        """extract multiple purchase order references"""

        # single PO reference
        refs = self._extract_refs("PO0001")
        self.assertSetEqual(set(refs), {"PO0001"})

        # multiple references separated by comma
        refs = self._extract_refs("PO0001,PO0002")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002"})

        # multiple references separated by semicolon
        refs = self._extract_refs("PO0001;PO0002")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002"})

        # references prefixed with '#'
        refs = self._extract_refs("#PO0001,#PO0002")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002"})

        # mixed separators and '#' prefix
        refs = self._extract_refs("#PO0001 ; PO0002 / #PO0003")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002", "PO0003"})

        # references embedded in free text
        refs = self._extract_refs("invoice related to PO0001 and PO0002")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002"})

        # deduplicate extracted purchase order references
        refs = self._extract_refs("PO0001,#PO0001,PO0002,PO0001")
        self.assertSetEqual(set(refs), {"PO0001", "PO0002"})

        # empty string should return no references
        refs = self._extract_refs("")
        self.assertSetEqual(set(refs), set())

        # falsy value should return no references
        refs = self._extract_refs(False)
        self.assertSetEqual(set(refs), set())

        # extraction with custom static prefix
        self.env["ir.sequence"].search(
            [("code", "=", "purchase.order")], limit=1
        ).prefix = "ACH"
        refs = self._extract_refs("ACH0001,#ACH0001,ACH0002,ACH0001")
        self.assertSetEqual(set(refs), {"ACH0001", "ACH0002"})

        # extraction with dynamic prefix including year (ACH%(year)s/)
        self.env["ir.sequence"].search(
            [("code", "=", "purchase.order")], limit=1
        ).prefix = "ACH%(year)s/"
        refs = self._extract_refs(
            "ACH2026/0001,#ACH2026/0001,ACH2026/0002,ACH2026/0001"
        )
        self.assertSetEqual(set(refs), {"ACH2026/0001", "ACH2026/0002"})

    def test_15(self):
        """import with multi po"""
        self.product.default_code = "leasing001"
        product2 = self.env["product.product"].create(
            {
                "name": "test_product",
                "standard_price": 100,
                "default_code": "leasing002",
            }
        )
        self._create_purchase_order(self.product, name="PO0001")
        self._create_purchase_order(product2, name="PO0002")
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"],
            file_path="account_edi_ubl_cii_purchase_match/tests/test_files/"
            "bis3_bill_example_multi_po.xml",
        )
        inv_l1 = bill.invoice_line_ids.filtered(
            lambda line: line.product_id.code == "leasing001"
        )
        inv_l2 = bill.invoice_line_ids.filtered(
            lambda line: line.product_id.code == "leasing002"
        )
        self.assertEqual(inv_l1.product_id, self.product)
        self.assertEqual(inv_l2.product_id, product2)
        self.assertEqual(inv_l1.purchase_line_id.order_id.name, "PO0001")
        self.assertEqual(inv_l2.purchase_line_id.order_id.name, "PO0002")

    def test_16(self):
        """match wizard should propose multiple PO"""
        product2 = self.env["product.product"].create(
            {"name": "test_product", "standard_price": 100}
        )
        self._create_purchase_order(self.product, name="PO0001")
        self._create_purchase_order(product2, name="PO0002")
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"],
            file_path="account_edi_ubl_cii_purchase_match/tests/test_files/"
            "bis3_bill_example_multi_po.xml",
        )
        self.assertEqual(len(bill.invoice_line_ids), 2)
        self.assertFalse(bill.invoice_line_ids.product_id)
        self.assertFalse(bill.invoice_line_ids.purchase_line_id)
        inv_l1 = bill.invoice_line_ids[0]
        action = inv_l1.action_select_purchase_line()
        wizard = (
            self.env[action.get("res_model")]
            .with_context(**action.get("context"))
            .create({})
        )
        self.assertEqual(len(wizard.purchase_order_ids), 2)
        self.assertSetEqual(
            set(wizard.purchase_order_ids.mapped("name")), {"PO0002", "PO0001"}
        )
