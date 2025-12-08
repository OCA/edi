from odoo import api, models


class AccountMove(models.Model):
    _inherit = ["account.move", "account.invoice.import.simple.pdf.mixin"]
    _name = "account.move"

    def _get_edi_decoder(self, file_data, new=False):
        if self.env.context.get("account_edi_simple_pdf_disable"):
            return super()._get_edi_decoder(file_data, new=new)

        specific_decoder = self.with_context(
            account_edi_simple_pdf_disable=True
        )._get_edi_decoder(file_data, new=new)
        return specific_decoder or (
            file_data["type"] == "pdf" and self._simple_pdf_edi_decoder
        )

    def _simple_pdf_edi_decoder(self, invoice, file_data, new):
        invoice._simple_pdf_amend_invoice_from_bytes(file_data["content"], new=new)

    def _simple_pdf_amend_invoice_from_bytes(self, attachment_bytes, **kwargs):
        parsed_values = self.simple_pdf_parse_invoice(attachment_bytes)

        if parsed_values.get("partner"):
            journal = self.journal_id
            currency = (
                parsed_values.get("currency", {}).get(
                    "recordset", self.env["res.currency"]
                )
                or self.currency_id
            )
            tax = self.env["account.tax"]
            amount_untaxed = currency.round(
                parsed_values.get(
                    "amount_untaxed",
                    parsed_values.get("amount_total", 0)
                    - parsed_values.get("amount_tax", 0),
                )
            )
            amount_tax = currency.round(
                parsed_values.get(
                    "amount_tax",
                    parsed_values.get("amount_total", 0)
                    - parsed_values.get("amount_untaxed", 0),
                )
            )
            if amount_untaxed and amount_tax:
                tax = self._simple_pdf_find_tax(
                    currency.round(amount_tax / amount_untaxed) * 100, journal.type
                )
            self.write(
                {
                    "currency_id": currency.id,
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
                                "tax_ids": [(6, 0, tax.ids)],
                            },
                        ),
                    ],
                }
            )
            self._onchange_partner_id()
            if self.partner_id.simple_pdf_product_id:
                line = self.invoice_line_ids[:1]
                line.write(
                    {
                        "product_id": self.partner_id.simple_pdf_product_id.id,
                        "name": parsed_values.get("description", line.name),
                        "price_unit": amount_untaxed or line.price_unit,
                    }
                )
            for message in parsed_values.get("chatter_msg", []):
                self.message_post(body=message)

    def _simple_pdf_find_tax(self, tax_amount, journal_type):
        return self.env["account.tax"].search(
            [
                ("amount", "=", tax_amount),
                ("type_tax_use", "=", journal_type),
                ("price_include", "=", False),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        result = super().message_new(msg_dict, custom_values=custom_values)
        for attachment_tuple in msg_dict.get("attachments", []):
            try:
                with self.env.cr.savepoint():
                    result._simple_pdf_amend_invoice_from_bytes(
                        attachment_tuple[1], new=True
                    )
            except Exception:  # pylint: disable=except-pass
                pass
        return result
