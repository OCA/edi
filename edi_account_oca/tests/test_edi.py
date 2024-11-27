# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from datetime import datetime

from odoo import fields

from odoo.addons.account.tests.account_test_no_chart import TestAccountNoChartCommon
from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import SavepointComponentRegistryCase

_logger = logging.getLogger(__name__)


class EDIBackendTestCase(TestAccountNoChartCommon, SavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpAdditionalAccounts()
        cls.setUpAccountJournal()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.cash_journal = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.env.user.company_id.id)]
        )[0]
        cls.journal_sale.update_posted = True

        class AccountInvoiceEventListenerDemo(Component):
            _name = "account.invoice.event.listener.demo"
            _inherit = "base.event.listener"

            def on_open_account_invoice(self, invoice):
                invoice.name = "new_name"

            def on_paid_account_invoice(self, invoice):
                invoice.name = "paid"

            def on_cancel_account_invoice(self, invoice):
                invoice.name = "cancelled"

        AccountInvoiceEventListenerDemo._build_component(cls.comp_registry)
        cls.comp_registry._cache.clear()
        cls.test_invoice = (
            cls.env["account.invoice"]
            .with_context(components_registry=cls.comp_registry)
            .create(
                {
                    "partner_id": cls.partner_customer_usd.id,
                    "date_invoice": fields.Date.from_string("2016-01-01"),
                    "journal_id": cls.journal_sale.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 1",
                                "account_id": cls.account_revenue.id,
                                "quantity": 1.0,
                                "price_unit": 100.0,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 2",
                                "account_id": cls.account_revenue.id,
                                "quantity": 1.0,
                                "price_unit": 100.0,
                            },
                        ),
                    ],
                }
            )
        )
        cls.test_invoice.refresh()

    def test_paid_move(self):
        self.test_invoice.action_invoice_open()
        self.assertEqual(self.test_invoice.name, "new_name")

        invoice_ctx = {
            "active_model": "account.invoice",
            "active_ids": [self.test_invoice.id],
        }
        register_payments = (
            self.env["account.register.payments"]
            .with_context(invoice_ctx)
            .create(
                {
                    "payment_date": datetime.now().strftime("%Y-%m-%d"),
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "journal_id": self.cash_journal.id,
                    "amount": 200.0,
                }
            )
        )
        register_payments.with_context(
            components_registry=self.comp_registry
        ).create_payments()
        self.assertEqual(self.test_invoice.name, "paid")

    def test_cancel_move(self):
        self.test_invoice.action_invoice_open()
        self.assertEqual(self.test_invoice.name, "new_name")
        self.test_invoice.action_cancel()
        self.assertEqual(self.test_invoice.name, "cancelled")
