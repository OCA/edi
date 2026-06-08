# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountEdiRetrievePartnerFromPurchaseOrder(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "standard_price": 100}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "ALD Automotive LU", "vat": "LU25587702"}
        )
        cls.po_partner = cls.env["res.partner"].create({"name": "Purchase partner"})
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.po_partner.id,
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
                "account_edi_retrieve_partner_from_purchase_order/tests/test_files/"
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
        Default behavior: the partner is matched with name
        """
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertEqual(bill.partner_id, self.partner)

    def test_1(self):
        """
        If a po is found, the po partner is set
        """
        self.purchase_order.partner_ref = "FAC/2023/00052"
        bill = self._import_invoice(self.company_data["default_journal_purchase"])
        self.assertEqual(bill.invoice_origin, "FAC/2023/00052")
        self.assertEqual(bill.partner_id, self.po_partner)
