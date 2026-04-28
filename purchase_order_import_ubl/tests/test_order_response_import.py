# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from pathlib import Path

from odoo.exceptions import UserError

from odoo.addons.purchase_order_import.tests.common import TestOrderResponseImportCommon


class TestOrderResponseImport(TestOrderResponseImportCommon):
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
        path = Path("purchase_order_import_ubl/tests/files/order_response_tmpl.xml")
        cls.order_response_xml = path.read_bytes().decode()

    def _get_order_response_xml(
        self,
        order_response_code="AB",
        line_1_status_code="5",
        line_2_status_code="5",
    ):
        return self.order_response_xml.format(
            order_response_code=order_response_code,
            order_id=self.purchase_order.name,
            line_1_id=self.line1.id,
            line_1_qty=self.line1.product_qty,
            line_1_backorder_qty=0,
            line_1_status_code=line_1_status_code,
            line_2_id=self.line2.id,
            line_2_qty=self.line2.product_qty,
            line_2_backorder_qty=0,
            line_2_status_code=line_2_status_code,
        ).encode()

    def test_parse_ubl_order_response(self):
        """Parse a UBL 2 OrderResponse document."""
        xml_content = self._get_order_response_xml(
            order_response_code=self.status_to_response_code["acknowledgement"],
            line_1_status_code=self.status_to_line_status["accepted"],
            line_2_status_code=self.status_to_line_status["accepted"],
        )
        result = self.OrderResponseImport.parse_order_response(xml_content, "test.xml")
        attachments = result.pop("attachments")
        self.assertTrue(attachments.get("test.xml"))
        expected = {
            "status": "acknowledgement",
            "company": {"vat": "BE0421801233"},
            "currency": {"iso": "EUR"},
            "date": "2020-02-04",
            "chatter_msg": [],
            "lines": [
                {
                    "status": "accepted",
                    "backorder_qty": 0,
                    "qty": self.line1.product_qty,
                    "note": "line_1 Note1\nline_1 Note2",
                    "line_id": str(self.line1.id),
                    "uom": {"unece_code": "C62"},
                },
                {
                    "status": "accepted",
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

    def test_unknown_response_code(self):
        """Raise a clear error for unsupported UBL response codes."""
        xml_content = self._get_order_response_xml(order_response_code="XX")
        with self.assertRaises(UserError) as error:
            self.OrderResponseImport.parse_order_response(xml_content, "test.xml")
        self._assert_user_error_message(
            error,
            self.env._("Unknown response code found '%(code)s'", code="XX"),
        )

    def test_unknown_line_status_code(self):
        """Raise a clear error for unsupported UBL line status codes."""
        xml_content = self._get_order_response_xml(line_1_status_code="XX")
        with self.assertRaises(UserError) as error:
            self.OrderResponseImport.parse_order_response(xml_content, "test.xml")
        self._assert_user_error_message(
            error,
            self.env._("Unsupported line status code found '%(code)s'", code="XX"),
        )
