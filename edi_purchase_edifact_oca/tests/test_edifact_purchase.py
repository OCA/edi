# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from odoo.addons.component.tests.common import TransactionComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin

from odoo import fields
from base64 import b64encode
import re


class TestEdifactPurchaseOrder(TransactionComponentCase, EDIBackendTestMixin):
    def setUp(self):
        super(TestEdifactPurchaseOrder, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.base_edifact_model = self.env["base.edifact"]
        self.company = self.env.ref("base.main_company")
        self.product_1 = self.env.ref("product.product_product_1")
        self.product_1.default_code = "FURN_6666"
        self.product_2 = self.env.ref("product.product_product_4")
        self.product_2.default_code = "FURN_8855"
        partner_id_number = self.env["res.partner.id_number"]
        self.partner_1 = self.env.ref("base.res_partner_1")
        self.partner_1.edifact_purchase_order_out = True
        self.partner_2 = self.env.ref("base.res_partner_12")
        self.exc_type_input = self.env.ref(
            "edi_purchase_edifact_oca.edi_exchange_type_purchase_order_input"
        )
        partner_id_number_data_1 = {
            "category_id": self.env.ref(
                "partner_identification_gln.partner_identification_gln_number_category"
            ).id,
            "partner_id": self.partner_1.id,
            "name": "9780201379624",
        }

        partner_id_number_data_2 = {
            "category_id": self.env.ref(
                "partner_identification_gln.partner_identification_gln_number_category"
            ).id,
            "partner_id": self.partner_2.id,
            "name": "9780201379174",
        }
        partner_id_number.create(partner_id_number_data_1)
        partner_id_number.create(partner_id_number_data_2)
        self.env.user.partner_id = self.partner_2
        self.env.user.company_id.partner_id = self.partner_2

        self.datetime = fields.Datetime.now()
        self.purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_1.id,
                "date_order": self.datetime,
                "date_planned": self.datetime,
            }
        )
        self.po_line1 = self.purchase.order_line.create(
            {
                "order_id": self.purchase.id,
                "product_id": self.product_1.id,
                "name": self.product_1.name,
                "date_planned": self.datetime,
                "product_qty": 12,
                "product_uom": self.product_1.uom_id.id,
                "price_unit": 42.42,
            }
        )
        self.po_line2 = self.purchase.order_line.create(
            {
                "order_id": self.purchase.id,
                "product_id": self.product_2.id,
                "name": self.product_2.name,
                "date_planned": self.datetime,
                "product_qty": 2,
                "product_uom": self.product_2.uom_id.id,
                "price_unit": 12.34,
            }
        )

    def test_edifact_purchase_generate_data(self):
        edifact_data = self.purchase.edifact_purchase_generate_data()
        self.assertTrue(edifact_data)
        self.assertEqual(isinstance(edifact_data, str), True)

    def test_edifact_purchase_get_interchange(self):
        interchange = self.purchase._edifact_purchase_get_interchange()
        self.assertEqual(interchange.sender, ["9780201379174", "14"])
        self.assertEqual(interchange.recipient, ["9780201379624", "14"])
        self.assertEqual(interchange.syntax_identifier, ["UNOC", "3"])

    def test_edifact_purchase_get_header(self):
        segments = self.purchase._edifact_purchase_get_header()
        seg = ("UNH", "", ["ORDERS", "D", "96A", "UN", "EAN008"])
        self.assertEqual(segments[0], seg)
        self.assertEqual(len(segments), 19)

    def test_edifact_purchase_get_product(self):
        segments, vals = self.purchase._edifact_purchase_get_product()
        self.assertEqual(len(segments), 22)
        self.assertEqual(len(vals), 2)

    def test_edifact_purchase_get_summary(self):
        vals = {"total_line_item": 2}
        segments = self.purchase._edifact_purchase_get_summary(vals)
        self.assertEqual(len(segments), 3)

    def test_edifact_purchase_get_address(self):
        partner = self.purchase.partner_id
        if hasattr(partner, "street3"):
            partner.street3 = "Address"
            self.assertEqual(
                self.purchase._edifact_purchase_get_address(partner), partner.street3
            )
        else:
            self.assertEqual(
                self.purchase._edifact_purchase_get_address(partner), partner.street
            )

    def test_action_confirm(self):
        self.purchase.button_confirm()
        exchange_record = self.env["edi.exchange.record"].search(
            [
                ("model", "=", "purchase.order"),
                ("res_id", "=", self.purchase.id),
            ]
        )
        exchange_record.action_exchange_generate()
        self.assertNotEqual(exchange_record.exchange_file, False)
        self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
        self.assertEqual(exchange_record.exchanged_on, False)

        # Compare data after generating
        expected_data = self.purchase.edifact_purchase_generate_data()
        expected_data = expected_data.replace(
            "UNH++ORDERS", f"UNH+{exchange_record.id}+ORDERS"
        )
        # Add edi_exchange_record.id to UNT segment in expected_data
        pattern = r"(UNT\+[^']*\+)[^']*(?=(?:'|$))"
        expected_data = re.sub(
            pattern,
            lambda match: f"{match.group(1)}{exchange_record.id}",
            expected_data,
        )
        self.assertEqual(
            exchange_record.exchange_file, b64encode(expected_data.encode())
        )

    def test_edifact_purchase_wizard_import(self):
        self.partner_1.edifact_purchase_order_out = False
        edifact_data = self.purchase.edifact_purchase_generate_data()
        self.assertTrue(edifact_data)
        self.assertEqual(isinstance(edifact_data, str), True)
        edifact_data = edifact_data.replace("UNH++ORDERS", "UNH+1+DESADV")

        wiz = self.env["purchase.order.import"].create(
            {
                "import_type": "edifact",
                "order_file": base64.b64encode(edifact_data.encode()),
                "order_filename": "test_edifact.txt",
            }
        )
        self.assertEqual(self.purchase.state, "draft")
        # Import file to confirm purchase order
        wiz.import_order_button()
        self.assertEqual(self.purchase.state, "purchase")

    def test_edifact_purchase_exchange_record_input(self):
        self.partner_1.edifact_purchase_order_out = False
        edifact_data = self.purchase.edifact_purchase_generate_data()
        self.assertTrue(edifact_data)
        self.assertEqual(isinstance(edifact_data, str), True)
        edifact_data = edifact_data.replace("UNH++ORDERS", "UNH+1+DESADV")

        record = self.exc_type_input.backend_id.create_record(
            self.exc_type_input.code,
            {
                "edi_exchange_state": "input_received",
                "exchange_file": base64.b64encode(edifact_data.encode()),
            },
        )
        self.assertEqual(self.purchase.state, "draft")

        record.action_exchange_process()
        self.assertEqual(self.purchase.state, "purchase")
