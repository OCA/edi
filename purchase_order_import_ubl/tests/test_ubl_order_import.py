# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo.fields import Command
from odoo.tools import file_open

from odoo.addons.base.tests.common import BaseCommon


class TestUblOrderImport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # For the sake of testing:
        # - enable USD and EUR
        # - set the PO currency to EUR
        # - create products where the PO supplier is listed as seller
        # - set the PO supplier email to match the one in the PDF file
        (cls.env.ref("base.USD") + cls.env.ref("base.EUR")).action_unarchive()
        cls.po = cls.env.ref("purchase.purchase_order_4")
        cls.po.currency_id = cls.env.ref("base.EUR")
        cls.env["product.product"].create(
            [
                {
                    "name": f"Test Product ({code})",
                    "type": "consu",
                    "seller_ids": [
                        Command.create(
                            {
                                "partner_id": cls.po.partner_id.id,
                                "product_code": code,
                            }
                        )
                    ],
                }
                for code in ("PROD_DEL02", "MBi9", "E-COM07", "E-COM09")
            ]
        )
        cls.po.partner_id.email = "info@test_purchase_order_import_ubl.com"
        with file_open(
            "purchase_order_import_ubl/tests/samples/quote-PO00004.pdf", "rb"
        ) as f:
            cls.order_response_pdf = f.read()

    def test_ubl_order_import(self):
        wiz_obj = self.env["purchase.order.import"]
        wiz_vals = {
            "quote_file": base64.b64encode(self.order_response_pdf),
            "quote_filename": "quote-PO00004.pdf",
        }
        wiz = wiz_obj.with_context(default_purchase_id=self.po.id).create([wiz_vals])
        self.assertEqual(wiz.purchase_id, self.po)
        wiz.update_rfq_button()
        self.assertEqual(self.po.incoterm_id, self.env.ref("account.incoterm_EXW"))
