# Copyright 2024 CamptoCamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import mock

from odoo.exceptions import UserError

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentRegistryTestCase


class TestsPurchaseEDIConfiguration(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load_module_components(cls, "edi_purchase_oca")
        cls.edi_configuration = cls.env["edi.configuration"]
        cls.purchase_order = cls.env["purchase.order"]
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "default_code": "1234567",
            }
        )

    def setUp(self):
        super().setUp()
        self.confirm_conf = self.env.ref(
            "edi_purchase_oca.edi_conf_button_confirm_purchase_order"
        )
        self.partner.write({"edi_purchase_conf_ids": [(4, self.confirm_conf.id)]})

    def test_edi_configuration_snippet_before_do(self):
        order = self.purchase_order.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        self.assertTrue(order)
        self.assertEqual(order.state, "draft")

        # Replace snippet_before_do for test
        self.confirm_conf.snippet_before_do = "record.button_cancel()"
        order.button_confirm()
        # After purchase order is confirmed
        # it will be automatically canceled due to edi_configuration execution.
        self.assertEqual(order.state, "cancel")

    def test_edi_configuration_snippet_do(self):
        self.confirm_conf.write(
            {
                "backend_id": self.backend.id,
                "type_id": self.exchange_type_out.id,
                "snippet_do": "record._edi_send_via_edi(conf.type_id)",
            }
        )
        with mock.patch.object(
            type(self.backend), "exchange_generate", return_value=True
        ):

            with self.assertRaises(UserError) as err:
                order = self.purchase_order.create(
                    {
                        "partner_id": self.partner.id,
                        "order_line": [
                            (
                                0,
                                0,
                                {
                                    "product_id": self.product.id,
                                    "product_qty": 10,
                                    "price_unit": 100.0,
                                },
                            )
                        ],
                    }
                )
                order.button_confirm()
            self.assertRegex(
                err.exception.args[0], r"Record ID=\d+ has no file to send!"
            )
