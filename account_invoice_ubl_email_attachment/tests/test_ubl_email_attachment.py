# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase
from odoo.tools import mute_logger


class TestUblInvoiceEmailAttachment(HttpCase):
    def setUp(self):
        super().setUp()

        partner = self.env.ref("base.res_partner_3")
        product = self.env.ref("product.product_product_5")
        acc_type_revenue = self.env.ref("account.data_account_type_revenue")
        account = self.env["account.account"].search(
            [("user_type_id", "=", acc_type_revenue.id)], limit=1
        )

        self.invoice = self.env["account.move"].create(
            {
                "name": "Test Customer Invoice",
                "type": "out_invoice",
                "partner_id": partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": 10.0,
                            "account_id": account.id,
                            "name": "product test",
                            "price_unit": 100.00,
                        },
                    )
                ],
            }
        )

        self.invoice.action_post()
        action_invoice_sent = self.invoice.action_invoice_sent()
        template_id = action_invoice_sent["context"]["default_template_id"]
        self.composer_ctx = dict(
            default_res_id=self.invoice.id,
            default_use_template=bool(template_id),
            default_composition_mode="comment",
            mark_invoice_as_sent=True,
            force_email=True,
        )
        self.composer_vals = {
            "attachment_ids": [],
            "model": "account.move",
            "record_name": False,
            "template_id": template_id,
        }

    def test_01_config(self):
        """Test configuration."""
        company = self.env.user.company_id
        conf = self.env["res.config.settings"].create(
            {"include_ubl_attachment_in_invoice_email": True}
        )
        conf.set_values()
        self.assertTrue(company.include_ubl_attachment_in_invoice_email)
        conf.write({"include_ubl_attachment_in_invoice_email": False})
        conf.set_values()
        self.assertFalse(company.include_ubl_attachment_in_invoice_email)

    @mute_logger("odoo.addons.base_ubl_payment.models.ubl")
    def test_02_ubl_invoice_email_no_attachment(self):
        conf = self.env["res.config.settings"].create(
            {"include_ubl_attachment_in_invoice_email": False}
        )
        conf.set_values()
        composer = (
            self.env["mail.compose.message"]
            .with_context(self.composer_ctx)
            .create(self.composer_vals)
        )
        self.assertFalse(composer.attachment_ids)
        composer.with_context(
            force_report_rendering=True
        ).onchange_template_id_wrapper()
        self.assertTrue(composer.attachment_ids)
        self.assertEqual(len(composer.attachment_ids), 1)

    @mute_logger("odoo.addons.base_ubl_payment.models.ubl")
    def test_03_ubl_invoice_email_no_attachment(self):
        conf = self.env["res.config.settings"].create(
            {"include_ubl_attachment_in_invoice_email": True}
        )
        conf.set_values()
        composer = (
            self.env["mail.compose.message"]
            .with_context(self.composer_ctx)
            .create(self.composer_vals)
        )
        self.assertFalse(composer.attachment_ids)
        composer.with_context(
            force_report_rendering=True
        ).onchange_template_id_wrapper()
        self.assertTrue(composer.attachment_ids)
        self.assertEqual(len(composer.attachment_ids), 1)

    @mute_logger("odoo.addons.base_ubl_payment.models.ubl")
    def test_04_ubl_invoice_email_with_attachment(self):
        conf = self.env["res.config.settings"].create(
            {"include_ubl_attachment_in_invoice_email": True}
        )
        conf.set_values()
        self.composer_ctx.update(attach_ubl_xml_file=True)
        composer = (
            self.env["mail.compose.message"]
            .with_context(self.composer_ctx)
            .create(self.composer_vals)
        )
        self.assertFalse(composer.attachment_ids)
        composer.with_context(
            force_report_rendering=True
        ).onchange_template_id_wrapper()
        self.assertTrue(composer.attachment_ids)
        self.assertEqual(len(composer.attachment_ids), 2)
