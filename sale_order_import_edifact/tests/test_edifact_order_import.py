# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import base64

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import get_test_data


class TestEdifactOrderImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_edifact_order_import(self):
        tests = get_test_data(self.env)
        for filename, expected in tests.items():
            edifact_file = expected._get_content()
            wiz = self.env["sale.order.import"].create(
                {
                    "import_type": "edifact",
                    "order_file": base64.b64encode(edifact_file),
                    "order_filename": filename,
                }
            )
            action = wiz.import_order_button()
            so = self.env["sale.order"].browse(action["res_id"])
            self.assertEqual(so.partner_id, expected["partner"])

            if expected.get("client_order_ref"):
                self.assertEqual(so.client_order_ref, expected["client_order_ref"])

            if expected.get("shipping_partner"):
                self.assertEqual(so.partner_shipping_id, expected["shipping_partner"])
            if expected.get("invoicing_partner"):
                self.assertEqual(so.partner_invoice_id, expected["invoicing_partner"])

            if expected.get("products"):
                expected_ids = sorted(expected["products"].ids)
                self.assertEqual(
                    sorted(so.order_line.mapped("product_id").ids), expected_ids
                )
