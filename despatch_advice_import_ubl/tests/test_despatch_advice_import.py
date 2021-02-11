# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import SavepointCase
from odoo.tools import file_open


class TestDespatchAdviceImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDespatchAdviceImport, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.supplier = cls.env.ref("base.res_partner_12")
        cls.supplier.vat = "BE0477472701"
        cls.env.user.company_id.partner_id.vat = "BE0421801233"
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "default_code": "1234567",
                "seller_ids": [(0, 0, {"name": cls.supplier.id, "product_code": "P1"})],
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "default_code": "2345678",
                "seller_ids": [(0, 0, {"name": cls.supplier.id, "product_code": "P2"})],
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
            }
        )
        cls.line1 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_1.id,
                "name": cls.product_2.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 24,
                "product_uom": cls.env.ref("product.product_uom_unit").id,
                "price_unit": 15,
            }
        )
        cls.line2 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_2.id,
                "name": cls.product_2.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 15,
                "product_uom": cls.env.ref("product.product_uom_unit").id,
                "price_unit": 25,
            }
        )
        cls.DespatchAdviceImport = cls.env["despatch.advice.import"]
        cls.ProcurementOrder = cls.env["procurement.order"]

        with file_open(
            "despatch_advice_import_ubl/tests/files/despatch_advice_tmpl.xml", "rb"
        ) as f:
            cls.despatch_advice_xml = f.read()

    def test_01(self):
        """
        Data:
            An UBL2 DespatchAdvice with all the information expected by the
            parser
        Test case:
            Convert to xml document to the internal data structure
        Expected result:
            All the fields are filled into the internal data structure.
        """
        xml_content = self.despatch_advice_xml.format(
            order_id=self.purchase_order.name,
            line_1_id=self.line1.id,
            line_1_qty=self.line1.product_qty,
            line_1_product_ref=self.product_1.default_code,
            line_1_backorder_qty=12,
            line_2_id=self.line2.id,
            line_2_qty=self.line2.product_qty,
            line_2_product_ref=self.product_2.default_code,
            line_2_backorder_qty=0,
        )
        result = self.DespatchAdviceImport.parse_despatch_advice(
            xml_content, "test.xml"
        )
        attachments = result.pop("attachments")
        self.assertTrue(attachments.get("test.xml"))
        expected = {
            "chatter_msg": [],
            "company": {"vat": "BE0421801233"},
            "date": "2020-11-16",
            "despatch_advice_type_code": "scheduled",
            "estimated_delivery_date": "2020-11-17",
            "lines": [
                {
                    "backorder_qty": 12,
                    "line_id": str(self.line1.id),
                    "product_ref": self.product_1.default_code,
                    "qty": self.line1.product_qty,
                    "uom": {"unece_code": "BG"},
                },
                {
                    "backorder_qty": None,
                    "line_id": str(self.line2.id),
                    "product_ref": self.product_2.default_code,
                    "qty": self.line2.product_qty,
                    "uom": {"unece_code": "C62"},
                },
            ],
            "ref": str(self.purchase_order.name),
            "supplier": {"vat": "BE0477472701"},
        }
        self.assertDictEqual(expected, result)
