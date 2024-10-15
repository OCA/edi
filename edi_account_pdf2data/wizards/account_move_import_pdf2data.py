# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tests.common import Form
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import format_amount

_logger = logging.getLogger(__name__)


class AccountMoveImportPdf2data(models.TransientModel):

    _name = "account.move.import.pdf2data"

    file = fields.Binary(attachment=True, required=True)
    filename = fields.Char()

    def import_file(self):
        extracted_text, data, template = (
            self.env["pdf2data.template"]
            .search(
                [
                    (
                        "type_id",
                        "=",
                        self.env.ref(
                            "edi_account_pdf2data.pdf2data_template_type_account_move"
                        ).id,
                    )
                ]
            )
            ._extract_pdf(self.file)
        )
        if data:
            return self._import_file_data(extracted_text, data, template)
        raise ValidationError(_("File cannot be processed. No templates found"))

    def _import_file_data(self, extracted_text, data, template):

        if not data.get("amount") and not data.get("amount_untaxed"):
            raise ValidationError(
                _("We need amount or amount untaxed in order to verify the invoice")
            )
        partner = self._get_partner(extracted_text, data, template)
        company = self._get_company(extracted_text, data, template) or self.env.company
        if not partner:
            raise ValidationError(_("Partner cannot be found"))
        invoice = Form(
            self.env["account.move"].with_context(
                default_company_id=company.id, default_type="in_invoice",
            )
        )
        invoice.partner_id = partner
        if data.get("date"):
            invoice.invoice_date = fields.Datetime.from_string(data.get("date"))
        modes = template.pdf2data_options_dict.get("mode", [])
        if not isinstance(modes, list):
            modes = [modes]
        for mode in modes:
            if hasattr(self, "_modify_form_move_%s" % mode):
                getattr(self, "_modify_form_move_%s" % mode)(
                    invoice, extracted_text, data, template
                )
        invoice = invoice.save()
        # This fields are done after the save of form in order to ensure that
        # all works as expected
        if data.get("invoice_number", False):
            invoice.ref = data["invoice_number"]
            invoice.invoice_payment_ref = data["invoice_number"]
        if data.get("due_date"):
            invoice.invoice_payment_term_id = self.env["account.payment.term"]
            invoice.invoice_date_due = fields.Datetime.from_string(data.get("due_date"))
        for mode in modes:
            if hasattr(self, "_modify_move_%s" % mode):
                getattr(self, "_modify_move_%s" % mode)(
                    invoice, extracted_text, data, template
                )
        self._validate_invoice(invoice, extracted_text, data, template)
        return invoice.get_formview_action()

    def _validate_invoice(self, invoice, extracted_text, data, template):
        errors = []
        if data.get("amount"):
            if float_compare(
                data.get("amount"),
                invoice.amount_total,
                precision_rounding=invoice.currency_id.rounding,
            ):
                errors.append(
                    _("Total Amount has a difference of %s")
                    % format_amount(
                        self.env,
                        invoice.currency_id.round(
                            data.get("amount") - invoice.amount_total
                        ),
                        invoice.currency_id,
                        self.env.user.lang,
                    )
                )
        message = [_("Invoice has been imported from a file import.")]
        if errors:
            message.append(_("<b>Some issues have been detected</b>"))
            message += errors
        invoice.message_post(body="<br/>".join(message),)

    def _get_product(self, line_data, template):
        return self.env["product.product"]

    def _modify_form_move_line(self, invoice, extracted_text, data, template):
        for line_data in data["lines"]:
            with invoice.invoice_line_ids.new() as line_form:
                product = self._get_product(line_data, template)
                if product:
                    line_form.product_id = product
                if line_data.get("description"):
                    line_form.name = line_data.get("description")
                line_form.quantity = line_data.get("qty", 1)
                if line_data.get("price_unit"):
                    line_form.price_unit = line_data.get("price_unit", 1)

    def _modify_form_move_purchase(self, invoice, extracted_text, data, template):
        sources = data.get("source")
        if not isinstance(sources, list):
            sources = [sources]
        for source in sources:
            purchase = self.env["purchase.order"].search(
                [
                    ("partner_id", "=", invoice.partner_id.id),
                    ("partner_ref", "=", source),
                    ("company_id", "=", invoice.company_id.id),
                ],
                limit=1,
            )
            if purchase:
                invoice.purchase_id = purchase

    def _get_partner(self, extracted_text, data, template):
        partner = self.env["res.partner"]
        if data.get("partner_vat"):
            partner = partner.search([("vat", "=", data["partner_vat"])], limit=1)
            if partner:
                return partner
        return partner

    def _get_company(self, extracted_text, data, template):
        company = self.env["res.company"]
        if data.get("company_vat"):
            company = company.search([("vat", "=", data["company_vat"])])
            if company:
                return company
        return company
