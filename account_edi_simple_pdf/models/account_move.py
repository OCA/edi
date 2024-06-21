from base64 import b64decode

from odoo import models
from odoo.tests.common import Form


class AccountMove(models.Model):
    _inherit = ["account.move", "account.invoice.import.simple.pdf.mixin"]
    _name = "account.move"

    def _get_create_invoice_from_attachment_decoders(self):
        return super()._get_create_invoice_from_attachment_decoders() + [
            (99, self._simple_pdf_create_invoice_from_attachment),
        ]

    def _simple_pdf_create_invoice_from_attachment(self, attachment):
        parsed_values = self.simple_pdf_parse_invoice(b64decode(attachment.datas))
        result = self.browse([])

        if parsed_values.get("partner"):
            self._get_default_journal()
            currency = self._get_default_currency()
            amount_untaxed = currency.round(
                parsed_values.get(
                    "amount_untaxed",
                    parsed_values.get("amount_total", 0)
                    - parsed_values.get("amount_tax", 0),
                )
            )
            result = self.create(
                {
                    "partner_id": parsed_values["partner"]
                    .get("recordset", self.env["res.partner"])
                    .id,
                    "invoice_date": parsed_values.get("date"),
                    "invoice_date_due": parsed_values.get("date_due"),
                    "ref": parsed_values.get("invoice_number"),
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": parsed_values.get("description", "/"),
                                "price_unit": amount_untaxed,
                            },
                        ),
                    ],
                }
            )
            if result.partner_id.simple_pdf_product_id:
                with Form(result) as invoice_form:
                    with invoice_form.invoice_line_ids.edit(0) as line_form:
                        line_form.product_id = result.partner_id.simple_pdf_product_id
                        line_form.name = parsed_values.get(
                            "description", line_form.name
                        )
                        line_form.price_unit = amount_untaxed or line_form.price_unit
        for message in parsed_values.get("chatter_msg", []):
            result.message_post(body=message)
        return result
