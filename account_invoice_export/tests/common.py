# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class CommonCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.send_exception = cls.env.ref(
            "account_invoice_export.mail_activity_transmit_warning"
        )
        cls.transmit_method = cls.env["transmit.method"].create(
            {
                "name": "HttpPost",
                "code": "httppost",
                "customer_ok": True,
                "send_through_http": True,
                "destination_url": "https://example.com/post",
                "destination_user": "user",
                "destination_pwd": "pwd",
            }
        )
        cls.customer = cls.partner
        cls.account = cls.company_data["default_account_revenue"]
        cls.invoice_1 = cls.env["account.move"].create(
            {
                "partner_id": cls.customer.id,
                "move_type": "out_invoice",
                "transmit_method_id": cls.transmit_method.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account.id,
                            "product_id": cls.product.id,
                            "name": "Product 1",
                            "quantity": 4.0,
                            "price_unit": 123.00,
                        },
                    )
                ],
            }
        )
        cls.invoice_1.action_post()
