# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

from odoo.tests.common import RecordCapturer, TransactionCase
from odoo.tools import file_open, mute_logger


class TestUblOrderImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_ubl_order_import_create_missing_invoice_partner(self):
        """Checks invoicing address street data"""
        filename = "UBL-Order-2.1-Example-CreateInvoicePartner.xml"
        file_path = "sale_order_import_ubl_address_extended/tests/files/" + filename
        with file_open(file_path, "rb") as f:
            xml_file = f.read()
        wiz = self.env["sale.order.import"].create(
            {
                "import_type": "xml",
                "order_file": base64.b64encode(xml_file),
                "order_filename": filename,
                "create_missing_invoice_partner": True,
            }
        )
        with RecordCapturer(self.env["res.partner"], []) as rc_partner:
            action = wiz.import_order_button()
        so = self.env["sale.order"].browse(action["res_id"])
        invoice_partner = so.partner_invoice_id
        self.assertEqual(rc_partner.records, invoice_partner)
        self.assertRecordValues(
            invoice_partner,
            [
                {
                    "street": "Invoice Street 6",
                    "street2": "Invoice floor",
                    "street_name": "Invoice Street",
                    "street_number": "6",
                    "street_number2": "",
                }
            ],
        )

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_ubl_order_import_create_missing_shipping_partner(self):
        """Tests the creation of delivery address when importing SO UBL files"""
        filename = "UBL-Order-2.1-Example-CreateShippingPartner.xml"
        file_path = "sale_order_import_ubl_address_extended/tests/files/" + filename
        with file_open(file_path, "rb") as f:
            xml_file = f.read()
        wiz = self.env["sale.order.import"].create(
            {
                "import_type": "xml",
                "order_file": base64.b64encode(xml_file),
                "order_filename": filename,
                "create_missing_shipping_partner": True,
            }
        )
        with RecordCapturer(self.env["res.partner"], []) as rc_partner:
            action = wiz.import_order_button()
        so = self.env["sale.order"].browse(action["res_id"])
        shipping_partner = so.partner_shipping_id
        self.assertEqual(rc_partner.records, shipping_partner)
        self.assertRecordValues(
            shipping_partner,
            [
                {
                    "street": "Delivery Street 7",
                    "street2": "Delivery floor",
                    "street_name": "Delivery Street",
                    "street_number": "7",
                    "street_number2": "",
                }
            ],
        )
