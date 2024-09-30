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

        confirm_conf = self.env.ref(
            "edi_purchase_oca.edi_conf_button_confirm_purchase_order"
        )
        # Replace snippet_before_do for test
        confirm_conf.snippet_before_do = "record.button_cancel()"

        order.button_confirm()
        # After purchase order is confirmed
        # it will be automatically canceled due to edi_configuration execution.
        self.assertEqual(order.state, "cancel")

    def test_edi_configuration_snippet_do(self):
        self.create_config = self.edi_configuration.create(
            {
                "name": "Create Config",
                "active": True,
                "code": "create_config",
                "backend_id": self.backend.id,
                "type_id": self.exchange_type_out.id,
                "trigger": "on_record_create",
                "model": self.env["ir.model"]._get_id("purchase.order"),
                "snippet_do": "record._edi_send_via_edi(conf.type_id)",
            }
        )
        with mock.patch.object(
            type(self.backend), "exchange_generate", return_value=True
        ):

            with self.assertRaises(UserError) as err:
                self.purchase_order.create(
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
            self.assertRegex(
                err.exception.args[0], r"Record ID=\d+ has no file to send!"
            )
