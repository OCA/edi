# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase


class TestPunchoutIdsCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.session_model = cls.env["punchout.session"]
        cls.backend = cls.backend_model.create(
            {
                "name": str(uuid4()),
                "description": str(uuid4()),
                "protocol": "ids",
                "url": "https://supplier.example.com/ids",
                "browser_form_post_url": "/punchout/ids/receive/",
                # IDS-specific fields
                "ids_version": "2.5",
                "ids_name_kunde": "TestCustomer",
                "ids_kndnr": "CUST001",
                "ids_pw_kunde": "secret",
            }
        )

        cls.session = cls.session_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": str(uuid4()),
            }
        )

    def _get_sample_ids_xml(self):
        """Return sample IDS shopping cart XML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<IDS>
    <Order>
        <OrderInfo>
            <Cur>EUR</Cur>
            <DeliveryDate>2025-01-15</DeliveryDate>
        </OrderInfo>
        <OrderItem>
            <ArtNo>12345</ArtNo>
            <Kurztext>Schraubendreher Set</Kurztext>
            <Qty>2</Qty>
            <QU>ST</QU>
            <NetPrice>29.99</NetPrice>
            <VAT>19</VAT>
        </OrderItem>
        <OrderItem>
            <ArtNo>67890</ArtNo>
            <Kurztext>Hammer 500g</Kurztext>
            <Qty>1</Qty>
            <QU>ST</QU>
            <NetPrice>15.50</NetPrice>
            <VAT>19</VAT>
            <EAN>4001234567890</EAN>
        </OrderItem>
    </Order>
</IDS>"""
