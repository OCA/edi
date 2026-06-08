# Copyright 2026 ACSONE SA/NV, BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountEdiUblCiiPurchaseMatchProductPackaging(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()
        cls.env.user.groups_id += cls.env.ref("product.group_stock_packaging")
        cls.env["ir.config_parameter"].set_param(
            "account_edi.product_name_match", "True"
        )
        cls.env["ir.sequence"].search(
            [("code", "=", "purchase.order")], limit=1
        ).prefix = "PO"
        cls.partner = cls.env["res.partner"].create(
            {"name": "ALD Automotive LU", "vat": "LU25587702"}
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.unece_packaging_type_x8a = cls.env["unece.code.list"].create(
            {
                "type": "packaging_type",
                "code": "X8A",
                "name": "Pallet, wooden",
                "description": "Wooden pallet.",
            }
        )
        cls.packaging_level = cls.env["product.packaging.level"].create(
            {
                "name": "Pallet",
                "code": "PAL",
                "sequence": 2,
                "unece_type_ids": [Command.set(cls.unece_packaging_type_x8a.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Locations and leasing",
                "type": "consu",
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "name": "PO00101",
                "order_line": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_qty": 1,
                            "price_unit": 1000,
                        }
                    ),
                ],
            }
        )
        cls.purchase_order.button_confirm()
        cls.po_line = cls.purchase_order.order_line

    def _import_invoice(self, journal, file_path):
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
        the UNECE unit code from the UBL file is stored on the invoice inv_line during import
        """
        file_path = (
            "account_edi_ubl_cii_purchase_match_product_packaging/tests/test_files/"
            "bis3_bill_example_uom_dozen.xml"
        )
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], file_path
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.ubl_unece_unit_code, "DPC")
        self.assertAlmostEqual(inv_line.ubl_price_unit, 657.0)
        self.assertAlmostEqual(inv_line.price_unit, 657.0)

    def test_1(self):
        """
        If the UNECE code can't be matched to a uom at import time,
        it is still stored and later used during reconciliation to recover and apply
        the correct uom once available
        """
        self.uom_dozen.unece_code = False
        file_path = (
            "account_edi_ubl_cii_purchase_match_product_packaging/tests/test_files/"
            "bis3_bill_example_uom_dozen.xml"
        )
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], file_path
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.ubl_unece_unit_code, "DPC")
        self.assertEqual(inv_line.product_uom_id, self.uom_unit)
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
        self.uom_dozen.unece_code = "DPC"
        wizard.select_purchase_line()
        self.assertEqual(inv_line.product_uom_id, self.uom_dozen)
        self.assertAlmostEqual(inv_line.ubl_price_unit, 657.0)
        self.assertAlmostEqual(inv_line.price_unit, 657.0)

    def test_2(self):
        """
        check that packaging is correctly applied during reconciliation when available
        """
        file_path = (
            "account_edi_ubl_cii_purchase_match_product_packaging/tests/test_files/"
            "bis3_bill_example_packaging_pallet.xml"
        )
        bill = self._import_invoice(
            self.company_data["default_journal_purchase"], file_path
        )
        inv_line = bill.invoice_line_ids
        self.assertEqual(inv_line.ubl_unece_unit_code, "X8A")
        self.assertEqual(inv_line.quantity, 1)
        self.assertEqual(inv_line.product_uom_id, self.uom_unit)
        self.assertFalse(inv_line.product_packaging_qty)
        self.assertFalse(inv_line.product_packaging_id)
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
        packaging = self.env["product.packaging"].create(
            {
                "name": "pallet 72",
                "product_id": self.product.id,
                "qty": 72.0,
                "packaging_level_id": self.packaging_level.id,
            }
        )
        wizard.select_purchase_line()
        self.assertEqual(inv_line.quantity, 72)
        self.assertEqual(inv_line.product_uom_id, self.uom_unit)
        self.assertEqual(inv_line.product_packaging_qty, 1)
        self.assertEqual(inv_line.product_packaging_id, packaging)
        self.assertAlmostEqual(inv_line.ubl_price_unit, 657.0)
        self.assertAlmostEqual(inv_line.price_unit, 9.13)
        return inv_line

    def test_3(self):
        inv_line = self.test_2()
        packaging = inv_line.product_packaging_id
        packaging.qty = 100
        action = inv_line.action_select_purchase_line()
        wizard = (
            self.env[action.get("res_model")]
            .with_context(**action.get("context"))
            .create({})
        )
        wizard.select_purchase_line()
        self.assertEqual(inv_line.quantity, 100)
        self.assertEqual(inv_line.product_uom_id, self.uom_unit)
        self.assertEqual(inv_line.product_packaging_qty, 1)
        self.assertEqual(inv_line.product_packaging_id, packaging)
        self.assertAlmostEqual(inv_line.ubl_price_unit, 657.0)
        self.assertAlmostEqual(inv_line.price_unit, 6.57)
