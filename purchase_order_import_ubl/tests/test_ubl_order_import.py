# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from pathlib import Path

from odoo.fields import Domain

from odoo.addons.purchase_order_import.tests.common import TestOrderResponseImportCommon


class TestUblOrderImport(TestOrderResponseImportCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PurchaseOrderImport = cls.env["purchase.order.import.wizard"]
        cls.supplier_delta = cls.env["res.partner"].create(
            {
                "name": "Delta PC",
                "supplier_rank": 1,
                "email": "info@yourcompany.example.com",
                "phone": "+1 555 123 8069",
            }
        )
        cls.incoterm_ddu = cls.env["account.incoterms"].create(
            {"name": "Delivered Duty Unpaid", "code": "DDU"}
        )
        cls.supplier = cls.supplier_delta
        cls.delta_products = {
            code: cls._get_or_create_delta_product(name, code)
            for code, name in (
                ("PROD_DEL02", "Datacard"),
                ("MBi9", "Motherboard I9P57"),
                ("E-COM07", "iPad Mini"),
                ("E-COM09", "iMac"),
            )
        }
        cls.purchase_order_delta = cls._create_purchase_order()
        cls.purchase_order_lines_delta = cls.env["purchase.order.line"]
        for product in cls.delta_products.values():
            cls.purchase_order_lines_delta |= cls._create_purchase_order_line(
                cls.purchase_order_delta,
                product,
                qty=1,
                price_unit=1,
            )

    @classmethod
    def _get_or_create_delta_product(cls, name, product_code):
        product = cls.env["product.product"].search(
            (
                Domain("company_id", "in", [cls.env.company.id, False])
                & (
                    Domain("barcode", "=", product_code)
                    | Domain("default_code", "=", product_code)
                )
            ),
            limit=1,
        )
        if product:
            return product
        product = cls._create_product(name, product_code)
        product.default_code = product_code
        return product

    def test_ubl_order_import_from_embedded_pdf(self):
        """Update an RFQ from a PDF with an embedded UBL quotation."""
        filename = "quote-PO00004.pdf"
        path = Path(f"purchase_order_import_ubl/tests/files/{filename}")
        quote_file = path.read_bytes()
        wiz = self.PurchaseOrderImport.with_context(
            active_model="purchase.order",
            active_id=self.purchase_order_delta.id,
        ).create(
            {
                "quote_file": b64encode(quote_file),
                "quote_filename": filename,
                "update_option": "all",
            }
        )
        self.assertEqual(wiz.purchase_id, self.purchase_order_delta)
        wiz.update_rfq_button()
        self.assertEqual(self.purchase_order_delta.incoterm_id, self.incoterm_ddu)
        expected_by_code = {
            "PROD_DEL02": (6.0, 90.0),
            "MBi9": (5.0, 1500.0),
            "E-COM07": (7.0, 330.0),
            "E-COM09": (1.0, 1799.0),
        }
        for line in self.purchase_order_delta.order_line:
            seller = line.product_id.seller_ids[:1]
            product_code = line.product_id.default_code or seller.product_code
            expected_qty, expected_price = expected_by_code[product_code]
            self.assertEqual(line.product_qty, expected_qty)
            self.assertEqual(line.price_unit, expected_price)
