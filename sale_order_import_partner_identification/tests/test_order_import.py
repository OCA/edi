# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger

from odoo.addons.sale_order_import.tests.common import TestCommon


class TestOrderImport(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Setup ID Category and Numbers
        id_categ_obj = cls.env["res.partner.id_category"]
        id_num_obj = cls.env["res.partner.id_number"]
        if id_categ := id_categ_obj.search([("code", "=", "GLN")], limit=1):
            # Clear all preexisting ID Numbers for the GLN ID Category
            # (prevent pollution and mismatching)
            id_num_obj.search([("category_id", "=", id_categ.id)]).unlink()
        else:
            # Create the GLN ID Category
            id_categ = id_categ_obj.create([{"name": "GLN", "code": "GLN"}])
        cls.partner_id_categ = id_categ

        # Setup parsed data to import
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
    def test_create_missing_invoice_partner_id_number(self):
        """Checks invoicing address street data"""
        parsed_order = self.parsed_order | dict(
            invoice_to={
                "name": "Test Invoice ID Number",
                "id_number": [{"schemeID": "GLN", "value": "INV-123"}],
            },
        )
        wiz = self.wiz_model.with_context(create_missing_invoice_partner=True)
        with (
            RecordCapturer(self.env["res.partner"], []) as rc_partner,
            RecordCapturer(self.env["res.partner.id_number"], []) as rc_id_number,
        ):
            so = wiz.create_order(parsed_order, "pricelist")
        invoice_partner = so.partner_invoice_id
        self.assertEqual(rc_partner.records, invoice_partner)
        self.assertRecordValues(
            rc_id_number.records,
            [
                {
                    "partner_id": invoice_partner.id,
                    "name": "INV-123",
                    "category_id": self.partner_id_categ.id,
                }
            ],
        )

    @mute_logger("odoo.addons.sale_order_import.wizard.sale_order_import")
    def test_create_missing_shipping_partner_id_number(self):
        """Checks invoicing address street data"""
        parsed_order = self.parsed_order | dict(
            ship_to={
                "name": "Test Shipping ID Number",
                "id_number": [{"schemeID": "GLN", "value": "SHIP-123"}],
            },
        )
        wiz = self.wiz_model.with_context(create_missing_shipping_partner=True)
        with (
            RecordCapturer(self.env["res.partner"], []) as rc_partner,
            RecordCapturer(self.env["res.partner.id_number"], []) as rc_id_number,
        ):
            so = wiz.create_order(parsed_order, "pricelist")
        shipping_partner = so.partner_shipping_id
        self.assertEqual(rc_partner.records, shipping_partner)
        self.assertRecordValues(
            rc_id_number.records,
            [
                {
                    "partner_id": shipping_partner.id,
                    "name": "SHIP-123",
                    "category_id": self.partner_id_categ.id,
                }
            ],
        )
