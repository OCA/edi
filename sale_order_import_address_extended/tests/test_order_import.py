# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger

from odoo.addons.sale_order_import.tests.common import TestCommon


class TestOrderImport(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parsed_order = {
            "partner": {"email": "so.import.test@example.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "FURN_8888"},
                    "qty": 2,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                }
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_create_missing_invoice_partner_address_extended(self):
        """Checks invoicing address street data"""
        parsed_order = dict(
            self.parsed_order,
            invoice_to={
                "country_code": "FR",
                "email": "test@invoice.partner",
                "name": "Test Invoice Address",
                "street": "Invoice Street 6",
                "street_name": "Invoice Street",
            },
        )
        wiz = self.wiz_model.with_context(create_missing_invoice_partner=True)
        with RecordCapturer(self.env["res.partner"], []) as rc_partner:
            so = wiz.create_order(parsed_order, "pricelist")
        invoice_partner = so.partner_invoice_id
        self.assertEqual(rc_partner.records, invoice_partner)
        self.assertRecordValues(
            invoice_partner,
            [
                {
                    "street": "Invoice Street 6",
                    "street_name": "Invoice Street",
                    "street_number": "6",
                    "street_number2": "",
                }
            ],
        )

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_order_import_create_missing_shipping_partner(self):
        """Checks shipping address street data"""
        parsed_order = dict(
            self.parsed_order,
            ship_to={
                "country_code": "FR",
                "email": "test@shipping.partner",
                "name": "Test Shipping Address",
                "street": "Shipping Street 6",
                "street_name": "Shipping Street",
            },
        )
        wiz = self.wiz_model.with_context(create_missing_shipping_partner=True)
        with RecordCapturer(self.env["res.partner"], []) as rc_partner:
            so = wiz.create_order(parsed_order, "pricelist")
        shipping_partner = so.partner_shipping_id
        self.assertEqual(rc_partner.records, shipping_partner)
        self.assertRecordValues(
            shipping_partner,
            [
                {
                    "street": "Shipping Street 6",
                    "street_name": "Shipping Street",
                    "street_number": "6",
                    "street_number2": "",
                }
            ],
        )
