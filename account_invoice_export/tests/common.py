# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import TransactionCase


class CommonCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        cls.country = cls.env.ref("base.ch")
        cls.customer = cls.env.ref("base.res_partner_1")
        cls.account = cls.env["account.account"].search(
            [("account_type", "=", "income"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        cls.product = cls.env.ref("product.product_product_1")
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
                            "product_id": cls.product.product_variant_ids[:1].id,
                            "name": "Product 1",
                            "quantity": 4.0,
                            "price_unit": 123.00,
                        },
                    )
                ],
            }
        )
        cls.invoice_1.action_post()
