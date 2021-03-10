# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields

from odoo.addons.account.tests.account_test_savepoint import AccountTestInvoicingCommon
from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import SavepointComponentRegistryCase

_logger = logging.getLogger(__name__)


class EDIBackendTestCase(AccountTestInvoicingCommon, SavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        class AccountMoveEventListenerDemo(Component):
            _name = "account.move.event.listener.demo"
            _inherit = "base.event.listener"

            def on_post_account_move(self, move):
                move.name = "new_name"

            def on_paid_account_move(self, move):
                move.name = "paid"

            def on_cancel_account_move(self, move):
                move.name = "cancelled"

        AccountMoveEventListenerDemo._build_component(cls.comp_registry)
        cls.comp_registry._cache.clear()
        cls.test_move = (
            cls.env["account.move"]
            .with_context(components_registry=cls.comp_registry)
            .create(
                {
                    "type": "out_invoice",
                    "partner_id": cls.partner_a.id,
                    "date": fields.Date.from_string("2016-01-01"),
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 1",
                                "account_id": cls.company_data[
                                    "default_account_revenue"
                                ].id,
                                "quantity": 1.0,
                                "price_unit": 100.0,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 2",
                                "account_id": cls.company_data[
                                    "default_account_revenue"
                                ].id,
                                "quantity": 1.0,
                                "price_unit": 100.0,
                                "tax_ids": [
                                    (6, 0, cls.company_data["default_tax_sale"].ids)
                                ],
                            },
                        ),
                    ],
                }
            )
        )
        cls.test_move.refresh()

    def test_paid_move(self):
        self.test_move.post()
        self.assertEqual(self.test_move.name, "new_name")

        payment_action = self.test_move.action_invoice_register_payment()
        payment = (
            self.env[payment_action["res_model"]]
            .with_context(**payment_action["context"])
            .create(
                {
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "journal_id": self.company_data["default_journal_bank"].id,
                }
            )
        )
        payment.with_context(components_registry=self.comp_registry).post()
        self.assertEqual(self.test_move.name, "paid")

    def test_cancel_move(self):
        self.test_move.post()
        self.assertEqual(self.test_move.name, "new_name")
        self.test_move.button_cancel()
        self.assertEqual(self.test_move.name, "cancelled")
