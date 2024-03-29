from odoo import _, api, models
from base64 import b64decode


class AccountMove(models.Model):
    _inherit = ["account.move", "account.invoice.import.simple.pdf.mixin"]
    _name = "account.move"

    def _get_create_invoice_from_attachment_decoders(self):
        return super()._get_create_invoice_from_attachment_decoders() + [
            (99, self._simple_pdf_create_invoice_from_attachment),
        ]

    def _simple_pdf_create_invoice_from_attachment(self, attachment):
        parsed_values = self.simple_pdf_parse_invoice(
            b64decode(attachment.datas)
        )
        result = self.browse([])

        if parsed_values.get('partner'):
            journal = self._get_default_journal()
            currency = self._get_default_currency()
            tax = self.env['account.tax']
            amount_untaxed = currency.round(
                parsed_values.get('amount_untaxed', parsed_values.get('amount_total', 0) - parsed_values.get('amount_tax', 0))
            )
            amount_tax = currency.round(
                parsed_values.get('amount_tax', parsed_values.get('amount_total', 0) - parsed_values.get('amount_untaxed', 0))
            )
            if amount_untaxed and amount_tax:
                tax = self.env['account.edi.format']._retrieve_tax(currency.round(amount_tax / amount_untaxed) * 100, journal.type)
            result = self.create({
                'partner_id': parsed_values['partner'].get('recordset', self.env['res.partner']).id,
                'invoice_date': parsed_values.get('date'),
                'invoice_date_due': parsed_values.get('date_due'),
                'ref': parsed_values.get('invoice_number'),
                'invoice_line_ids': [
                    (0, 0, {
                        'name': parsed_values.get('description', '/'),
                        'price_unit': parsed_values.get('amount_untaxed', parsed_values.get('amount_total', 0) - parsed_values.get('amount_tax', 0)),
                        'tax_ids': [(6, 0, tax.ids)],
                    }),
                ],
            })
        for message in parsed_values.get('chatter_msg', []):
            result.message_post(body=message)
        return result
