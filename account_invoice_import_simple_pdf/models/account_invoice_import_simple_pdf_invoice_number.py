# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

MAX_PAST_YEARS = 5

try:
    import regex
except ImportError:
    logger.debug("Cannot import regex")


class AccountInvoiceImportSimplePdfInvoiceNumber(models.Model):
    _name = "account.invoice.import.simple.pdf.invoice.number"
    _description = "Invoice number format for Simple PDF invoice import"
    _order = "sequence, id"

    partner_id = fields.Many2one("res.partner", string="Vendor", ondelete="cascade")
    sequence = fields.Integer(default=10)
    string_type = fields.Selection("_string_type_sel", string="Type", required=True)
    fixed_char = fields.Char()
    occurrence_min = fields.Integer(string="Minimum Occurence", default=1)
    occurrence_max = fields.Integer(string="Maximum Occurence", default=1)

    _sql_constraints = [
        (
            "occurrence_min_positive",
            "CHECK(occurrence_min > 0)",
            "The minimum occurence must be strictly positive.",
        ),
        (
            "occurrence_max_positive",
            "CHECK(occurrence_max > 0)",
            "The maximum occurence must be strictly positive.",
        ),
    ]

    @api.model
    def _string_type_sel(self):
        return [
            ("fixed", "Fixed"),
            ("letter_upper", "Upper Letter"),
            ("letter_lower", "Lower Letter"),
            ("digit", "Digit(s)"),
            ("space", "Space"),
            ("year2", "Year on 2 digits"),
            ("year4", "Year on 4 digits"),
            ("month", "Month (2 digits)"),
        ]

    @api.constrains("string_type", "fixed_char", "occurrence_min", "occurrence_max")
    def _check_invoice_number_format(self):
        for rec in self:
            if rec.string_type == "fixed":
                fixed_char_stripped = rec.fixed_char and rec.fixed_char.strip()
                if not fixed_char_stripped:
                    raise ValidationError(_("Missing fixed char."))
            elif rec.string_type in ("letter_upper", "letter_lower", "digit", "space"):
                if rec.occurrence_max < rec.occurrence_min:
                    raise ValidationError(
                        _(
                            "The maximum occurence (%d) must be equal to or above "
                            "the minimum occurence (%d)."
                        )
                        % (rec.occurrence_max, rec.occurrence_min)
                    )

    @api.onchange("occurrence_min")
    def occurrence_min_change(self):
        if self.occurrence_min > self.occurrence_max:
            self.occurrence_max = self.occurrence_min

    def _prepare_invoice_number_regex(self, regex_list):
        self.ensure_one()
        type2regex = {
            "letter_upper": "[A-Z]",
            "letter_lower": "[a-z]",
            "digit": r"\d",
            "space": r"\s",
        }
        if self.string_type == "fixed":
            regex_list.append(regex.escape(self.fixed_char.strip()))
        elif self.string_type in ("letter_upper", "letter_lower", "digit", "space"):
            if self.occurrence_min == self.occurrence_max:
                suffix = "{%d}" % self.occurrence_min
            else:
                suffix = "{%d,%d}" % (self.occurrence_min, self.occurrence_max)

            regex_list.append(type2regex[self.string_type] + suffix)
        elif self.string_type in ("year2", "year4"):
            # match on current and previous year only
            current_year = fields.Date.context_today(self).year

            years = [current_year - y for y in range(MAX_PAST_YEARS + 1)]
            if self.string_type == "year2":
                years_str = [str(y)[-2:] for y in years]
            else:
                years_str = [str(y) for y in years]
            regex_list.append("(?:%s)" % "|".join(years_str))
        elif self.string_type == "month":
            regex_list.append("(?:01|02|03|04|05|06|07|08|09|10|11|12)")
