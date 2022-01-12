# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, mute_logger


class TestUblOrderImport(TransactionCase):
    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_ubl_order_import(self):
        ref = self.env.ref
        tests = {
            "UBL-Order-2.1-Example.xml": {
                "client_order_ref": "34",
                "date_order": "2010-01-20",
                "partner": ref("sale_order_import_ubl.svensson"),
                "shipping_partner": ref("sale_order_import_ubl.swedish_trucking"),
                "invoicing_partner": ref("sale_order_import_ubl.karlsson"),
                "currency": ref("base.SEK"),
                "commitment_date": "2010-02-26 18:00:00",
                "products": ref("sale_order_import_ubl.product_red_paint")
                + ref("sale_order_import_ubl.product_pencil"),
            },
            "UBL-Order-2.0-Example.xml": {
                "client_order_ref": "AEG012345",
                "date_order": "2010-06-20",
                "partner": self.env.ref("sale_order_import_ubl.fred_churchill"),
                "shipping_partner": self.env.ref("sale_order_import_ubl.iyt"),
                "currency": self.env.ref("base.GBP"),
                "commitment_date": "2010-02-26 00:00:00",
                "products": ref("sale_order_import_ubl.product_beeswax"),
            },
            "UBL-RequestForQuotation-2.0-Example.xml": {
                "partner": self.env.ref("sale_order_import_ubl.s_massiah"),
                "shipping_partner": self.env.ref("sale_order_import_ubl.iyt"),
                "products": ref("sale_order_import_ubl.product_beeswax"),
            },
            "UBL-RequestForQuotation-2.1-Example.xml": {
                "partner": self.env.ref("sale_order_import_ubl.gentofte_kommune"),
                "currency": self.env.ref("base.DKK"),
                "shipping_partner": self.env.ref(
                    "sale_order_import_ubl.delivery_gentofte_kommune"
                ),
                "products": ref("product.product_product_25")
                + ref("product.product_product_24")
                + ref("product.product_product_9"),
            },
        }
        for filename, res in tests.items():
            f = file_open("sale_order_import_ubl/tests/files/" + filename, "rb")
            xml_file = f.read()
            wiz = self.env["sale.order.import"].create(
                {"order_file": base64.b64encode(xml_file), "order_filename": filename}
            )
            f.close()
            action = wiz.import_order_button()
            so = self.env["sale.order"].browse(action["res_id"])
            self.assertEqual(so.partner_id, res["partner"])
            if res.get("currency"):
                self.assertEqual(so.currency_id, res["currency"])
            if res.get("client_order_ref"):
                self.assertEqual(so.client_order_ref, res["client_order_ref"])
            if res.get("date_order"):
                date_order = fields.Datetime.to_string(so.date_order)
                self.assertEqual(date_order[:10], res["date_order"])
            if res.get("shipping_partner"):
                self.assertEqual(so.partner_shipping_id, res["shipping_partner"])
            if res.get("commitment_date"):
                self.assertEqual(
                    so.commitment_date.strftime("%Y-%m-%d %H:%M:%S"),
                    res["commitment_date"],
                )
            else:
                self.assertFalse(so.commitment_date)

            # NOTE: parsing products should be tested by base_ubl
            # but ATM there's no test coverage there.
            # This little test ensures that it works in this context at least.
            if res.get("products"):
                expected_ids = sorted(res["products"].ids)
                self.assertEqual(
                    sorted(so.order_line.mapped("product_id").ids), expected_ids
                )
