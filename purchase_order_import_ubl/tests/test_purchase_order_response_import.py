# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools import file_open

from odoo.addons.purchase_order_import.tests.test_purchase_order_response_import import (  # noqa: E501
    TestPurchaseOrderResponseImportCommon,
)
from odoo.addons.purchase_order_import.wizard.purchase_order_response_import import (
    LINE_STATUS_ACCEPTED,
    ORDER_RESPONSE_STATUS_ACK,
)


class TestPurchaseOrderResponseImport(TestPurchaseOrderResponseImportCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.status_to_response_code = {
            status: code
            for code, status in (
                cls.OrderResponseImport._order_response_code_to_status.items()
            )
        }
        cls.status_to_line_status = {
            status: code
            for code, status in (
                cls.OrderResponseImport._order_line_status_to_status.items()
            )
        }
        with file_open(
            "purchase_order_import_ubl/tests/samples/purchase_order_response_tmpl.xml",
            "rb",
        ) as f:
            cls.order_response_xml = f.read().decode()

    def test_01(self):
        """
        Data:
            An UBL2 OrderResponse with all the information expected by the
            parser
        Test case:
            Convert to xml document to the internal data structure
        Expected result:
            All the fields are filled into the internal data structure.
        """
        xml_content = self.order_response_xml.format(
            order_response_code=self.status_to_response_code[ORDER_RESPONSE_STATUS_ACK],
            order_id=self.purchase_order.name,
            line_1_id=self.line1.id,
            line_1_qty=self.line1.product_qty,
            line_1_backorder_qty=0,
            line_1_status_code=self.status_to_line_status[LINE_STATUS_ACCEPTED],
            line_2_id=self.line2.id,
            line_2_qty=self.line2.product_qty,
            line_2_backorder_qty=0,
            line_2_status_code=self.status_to_line_status[LINE_STATUS_ACCEPTED],
        ).encode()
        result = self.OrderResponseImport.parse_order_response(xml_content, "test.xml")
        attachments = result.pop("attachments")
        self.assertTrue(attachments.get("test.xml"))
        expected = {
            "status": ORDER_RESPONSE_STATUS_ACK,
            "company": {"vat": "BE0421801233"},
            "currency": {"iso": "EUR"},
            "date": "2020-02-04",
            "chatter_msg": [],
            "lines": [
                {
                    "status": LINE_STATUS_ACCEPTED,
                    "backorder_qty": 0,
                    "qty": self.line1.product_qty,
                    "note": "line_1 Note1\nline_1 Note2",
                    "line_id": str(self.line1.id),
                    "uom": {"unece_code": "C62"},
                },
                {
                    "status": LINE_STATUS_ACCEPTED,
                    "backorder_qty": 0,
                    "qty": self.line2.product_qty,
                    "note": "line_2 Note1\nline_2 Note2",
                    "line_id": str(self.line2.id),
                    "uom": {"unece_code": "C62"},
                },
            ],
            "note": "Note1\nNote2",
            "time": "22:10:30",
            "supplier": {"vat": "BE0401953350"},
            "ref": str(self.purchase_order.name),
        }
        self.assertDictEqual(expected, result)
