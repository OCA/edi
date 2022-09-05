# Copyright 2016 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import get_test_data


class TestUblOrderImport(TransactionCase):
    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_ubl_order_import(self):
        tests = get_test_data(self.env)
        for filename, expected in tests.items():
            xml_file = expected._get_content()
            wiz = self.env["sale.order.import"].create(
                {
                    "order_file": base64.b64encode(xml_file),
                    "order_filename": filename,
                }
            )
            action = wiz.import_order_button()
            so = self.env["sale.order"].browse(action["res_id"])
            self.assertEqual(so.partner_id, expected["partner"])
            if expected.get("currency"):
                self.assertEqual(so.currency_id, expected["currency"])
            if expected.get("client_order_ref"):
                self.assertEqual(so.client_order_ref, expected["client_order_ref"])
            if expected.get("date_order"):
                date_order = fields.Datetime.to_string(so.date_order)
                self.assertEqual(date_order[:10], expected["date_order"])
            if expected.get("shipping_partner"):
                self.assertEqual(so.partner_shipping_id, expected["shipping_partner"])
            if expected.get("invoicing_partner"):
                self.assertEqual(so.partner_invoice_id, expected["invoicing_partner"])
            if filename in ("UBL-Order-2.1-Example.xml", "UBL-Order-2.0-Example.xml"):
                self.assertTrue(expected.get("commitment_date"))
                self.assertEqual(
                    so.commitment_date.strftime("%Y-%m-%d %H:%M:%S"),
                    expected["commitment_date"],
                )
            else:
                self.assertFalse(so.commitment_date)

            # NOTE: parsing products should be tested by base_ubl
            # but ATM there's no test coverage there.
            # This little test ensures that it works in this context at least.
            if expected.get("products"):
                expected_ids = sorted(expected["products"].ids)
                self.assertEqual(
                    sorted(so.order_line.mapped("product_id").ids), expected_ids
                )
