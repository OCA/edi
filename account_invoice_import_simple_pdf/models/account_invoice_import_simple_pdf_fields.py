# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date

from .res_partner import ERROR_STYLE

logger = logging.getLogger(__name__)

try:
    import regex
except ImportError:
    logger.debug("Cannot import regex")
try:
    import dateparser
except ImportError:
    logger.debug("Cannot import dateparser")


class AccountInvoiceImportSimplePdfFields(models.Model):
    _name = "account.invoice.import.simple.pdf.fields"
    _description = "Fields for Simple PDF invoice import"
    _order = "partner_id, sequence, id"

    partner_id = fields.Many2one("res.partner", string="Vendor", ondelete="cascade")
    # the order has no impact, it's just for readability
    sequence = fields.Integer(default=10)
    name = fields.Selection(
        [
            ("amount_total", "Total"),
            ("amount_untaxed", "Untaxed Amount"),
            ("amount_tax", "Tax Amount"),
            ("date", "Invoice Date"),
            ("date_due", "Due Date"),
            ("date_start", "Start Date"),
            ("date_end", "End Date"),
            ("invoice_number", "Invoice Number"),
            ("description", "Description"),
        ],
        required=True,
        string="Field",
    )
    regexp = fields.Char(string="Specific Regular Expression")
    date_format = fields.Selection(
        "_date_format_sel",
        string="Specific Date Format",
        help="Leave empty if the format used is the same as the format defined "
        "in the global section.",
    )
    date_separator = fields.Selection(
        "_date_separator_sel",
        string="Specific Date Separator",
        help="Leave empty if the format used is the same as the format defined "
        "in the global section.",
    )
    start = fields.Char(string="Start String")
    end = fields.Char(string="End String")
    extract_rule = fields.Selection(
        [
            ("first", "First"),
            ("last", "Last"),
            ("position_start", "Specific Position from Start"),
            ("position_end", "Specific Position from End"),
            ("min", "Min"),
            ("max", "Max"),
            ("position_min", "Specific Position from Min"),
            ("position_max", "Specific Position from Max"),
        ],
        string="Extract Rule",
        required=True,
    )
    position = fields.Integer(default=2)

    @api.model
    def _date_format_sel(self):
        return self.env["res.partner"]._simple_pdf_date_format_sel()

    @api.model
    def _date_separator_sel(self):
        return self.env["res.partner"]._simple_pdf_date_separator_sel()

    _sql_constraints = [
        (
            "position_specific_positive",
            "CHECK(position > 0)",
            "The position must be strictly positive.",
        ),
        (
            "partner_field_unique",
            "unique(partner_id, name)",
            "There is already an entry for that field.",
        ),
    ]

    @api.constrains("name", "regexp")
    def _check_field_config(self):
        for field in self:
            if field.name == "description" and not field.regexp:
                raise ValidationError(
                    _(
                        "You must set a Specific Regular Expression on "
                        "the 'Description' field."
                    )
                )

    @api.onchange("name")
    def field_change(self):
        if not self.extract_rule:
            if self.name == "amount_total":
                self.extract_rule = "max"
            elif self.name in ("invoice_number", "description", "date"):
                self.extract_rule = "first"

    # This method is just 1 line over the complexity limit of C901
    # and I don't see a good way to split it
    def get_value_from_list(  # noqa: C901
        self, data_list, test_info, raise_if_none=True
    ):
        assert isinstance(data_list, list)
        if not data_list:
            if raise_if_none:
                raise UserError(
                    _("No valid data extracted for field '%s'.") % self.name
                )
            else:
                return None
        if self.extract_rule in ("min", "max", "position_min", "position_max"):
            data_list_sorted = list(data_list)
            data_list_sorted.sort()
            if self.name.startswith("date"):
                test_info[self.name]["sorted_list"] = [
                    format_date(self.env, date_dt) for date_dt in data_list_sorted
                ]
            else:
                test_info[self.name]["sorted_list"] = data_list_sorted
        if self.extract_rule == "max":
            return data_list_sorted[-1]
        elif self.extract_rule == "min":
            return data_list_sorted[0]
        elif self.extract_rule in ("position_min", "position_max"):
            if len(data_list) < self.position:
                error_msg = _(
                    "Partner '%s' is configured with an extract rule '%s' with "
                    "position %d for field '%s' but the list of "
                    "extracted valid data only has %d entries."
                ) % (
                    self.partner_id.display_name,
                    test_info["extract_rule_sel"][self.extract_rule],
                    self.position,
                    test_info["field_name_sel"][self.name],
                    len(data_list),
                )
                if raise_if_none:
                    raise UserError(error_msg)
                else:
                    test_info[self.name]["error_msg"] = error_msg
                    return None
            sign = self.extract_rule == "position_min" and 1 or -1
            position = self.position
            if self.extract_rule == "position_min":
                position -= 1
            return data_list[position * sign]
        elif self.extract_rule == "first":
            return data_list[0]
        elif self.extract_rule == "last":
            return data_list[-1]
        elif self.extract_rule in ("position_start", "position_end"):
            if len(data_list) < self.position:
                error_msg = _(
                    "Partner '%s' is configured with an extract rule '%s' with "
                    "position %d for field '%s' but the list of extracted "
                    "valid data only has %d entries."
                ) % (
                    self.partner_id.display_name,
                    test_info["extract_rule_sel"][self.extract_rule],
                    self.position,
                    test_info["field_name_sel"][self.name],
                    len(data_list),
                )
                if raise_if_none:
                    raise UserError(error_msg)
                else:
                    test_info[self.name]["error_msg"] = error_msg
                    return None
            sign = self.extract_rule == "position_start" and 1 or -1
            position = self.position
            if self.extract_rule == "position_start":
                position -= 1
            return data_list[position * sign]
        else:
            raise UserError(_("Bad configuration"))

    def restrict_text(self, raw_text, test_info):
        self.ensure_one()
        restrict_text = raw_text
        start = self.start and self.start.strip() or False
        end = self.end and self.end.strip() or False
        if start:
            position = restrict_text.find(start)
            if position >= 0:
                restrict_text = restrict_text[position + len(start) :]
                test_info[self.name]["start"] = _("Successful cut on '%s'") % start
            else:
                error_msg = _("String '%s' not found") % start
                test_info[self.name]["start"] = "<b%s>%s</b>" % (ERROR_STYLE, error_msg)
        if end:
            if not restrict_text or (restrict_text and not restrict_text.strip()):
                error_msg = _(
                    "No text to cut, maybe because start string "
                    "was the very end of the document"
                )
                test_info[self.name]["end"] = "<b%s>%s</b>" % (ERROR_STYLE, error_msg)
            else:
                position = restrict_text.find(end)
                if position >= 0:
                    restrict_text = restrict_text[:position]
                    test_info[self.name]["end"] = _("Successful cut on '%s'") % end
                else:
                    error_msg = _("String '%s' not found") % end
                    test_info[self.name]["end"] = "<b%s>%s</b>" % (
                        ERROR_STYLE,
                        error_msg,
                    )
        return restrict_text

    def _get_date(self, parsed_inv, raw_text, partner_config, test_info):
        date_format = self.date_format or partner_config["date_format"]
        error_arg = (
            partner_config["display_name"],
            test_info["field_name_sel"][self.name],
        )
        if not date_format:
            raise UserError(
                _("No date format configured on partner '%s' nor on the field '%s'.")
                % error_arg
            )
        date_separator = self.date_separator or partner_config["date_separator"]
        if not date_separator:
            raise UserError(
                _("No date separator configured on partner '%s' nor on the field '%s'.")
                % error_arg
            )
        date_separator_char = partner_config["separator2char"][date_separator]

        if self.regexp:
            pattern = self.regexp
        else:
            pattern = date_format
            for src, dest in partner_config["date_format2regex"].items():
                pattern = pattern.replace(src, dest)

            if date_separator_char == chr(32):
                date_separator_regex = ",?%s+" % test_info["space_pattern"]
            else:
                date_separator_regex = regex.escape(date_separator_char)

            pattern = pattern.replace("-", date_separator_regex)
        test_info[self.name] = {
            "pattern": pattern,
            "date_format": test_info["date_format_sel"][date_format].replace(
                " ", date_separator_char
            ),
        }
        restrict_text = self.restrict_text(raw_text, test_info)
        res_regex = regex.findall(pattern, restrict_text)
        valid_dates_dt = []
        date_formatdt = date_format
        for src, dest in partner_config["date_format2dt"].items():
            date_formatdt = date_formatdt.replace(src, dest)
        date_formatdt = date_formatdt.replace("-", date_separator_char)
        languages = (
            partner_config["lang_short"] and [partner_config["lang_short"]] or None
        )
        for date_raw in res_regex:
            date_dt = dateparser.parse(
                date_raw, date_formats=[date_formatdt], languages=languages
            )
            if date_dt:
                valid_dates_dt.append(date_dt)
            else:
                logger.debug(
                    "Failed to parse date %s using format %s and language %s",
                    date_raw,
                    date_formatdt,
                    partner_config["lang_short"],
                )
        test_info[self.name].update(
            {
                "res_regex": res_regex,
                "valid_list": [
                    format_date(self.env, vdate_dt) for vdate_dt in valid_dates_dt
                ],
            }
        )
        if self.name == "date_due" or test_info["test_mode"]:
            raise_if_none = False
        else:
            raise_if_none = True
        date_dt = self.get_value_from_list(
            valid_dates_dt, test_info, raise_if_none=raise_if_none
        )
        if date_dt:
            parsed_inv[self.name] = date_dt
        else:
            parsed_inv["failed_fields"].append(self.name)

    def _get_date_due(self, *args):
        return self._get_date(*args)

    def _get_date_start(self, *args):
        return self._get_date(*args)

    def _get_date_end(self, *args):
        return self._get_date(*args)

    def _get_amount_total(self, parsed_inv, raw_text, partner_config, test_info):
        thousand_sep = partner_config["thousand_sep"]
        if not thousand_sep:
            thousand_sep_pattern = ""
        elif thousand_sep == chr(32):
            thousand_sep_pattern = test_info["space_pattern"]
        else:
            thousand_sep_pattern = regex.escape(thousand_sep)
        decimal_sep = partner_config["decimal_sep"]
        decimal_sep_pattern = regex.escape(decimal_sep)
        decimal_places = partner_config["currency"].decimal_places
        if self.regexp:
            pattern = self.regexp
        else:
            if decimal_places:
                pattern = r"(?:\d{1,3}%s)*\d{1,3}%s\d{%d}" % (
                    thousand_sep_pattern,
                    decimal_sep_pattern,
                    decimal_places,
                )
            else:
                pattern = r"(?:\d{1,3}%s)*\d{1,3}" % thousand_sep_pattern
        test_info[self.name] = {"pattern": pattern}
        # don't take if followed by a % ? => means it's a rate
        restrict_text = self.restrict_text(raw_text, test_info)
        # I don't move the code that filters out percentrages and capital
        # to simple_pdf_text_extraction() because I want to have raw
        # test for start/end cut
        # filter out percentage with decimal like VAT rates or discounts
        # for example '5.5 %' or '20.0%'
        restrict_text_filtered = regex.sub(
            r"\d{1,2}%s\d{1,2}\s?%%" % regex.escape(decimal_sep), "", restrict_text
        )
        # filter out discounts or VAT rates without decimal e.g. 20%
        restrict_text_filtered = regex.sub(r"\d{1,3}\s?%", "", restrict_text_filtered)
        # Try to filter out capital amounts
        # Yes, this is a hack :)
        # Works in EN and FR... what about other languages ?
        restrict_text_filtered = regex.sub(
            r"[Cc]apital.{1,30}(?:\d{1,3}%s)*\d{1,3}" % regex.escape(thousand_sep),
            "",
            restrict_text_filtered,
        )
        res_regex = regex.findall(pattern, restrict_text_filtered)
        valid_amounts = []
        for amount_raw in res_regex:
            if thousand_sep_pattern:
                amount_raw = regex.sub(thousand_sep_pattern, "", amount_raw)
            if decimal_places:
                amount_raw_list = list(amount_raw)
                amount_raw_list[-decimal_places - 1] = "."
                amount_raw = "".join(amount_raw_list)
            try:
                valid_amounts.append(float(amount_raw))
            except ValueError:
                logger.debug("%s is an invalid float", amount_raw)
        test_info[self.name].update(
            {
                "res_regex": res_regex,
                "valid_list": valid_amounts,
            }
        )
        raise_if_none = not test_info["test_mode"] and True or False
        amount = self.get_value_from_list(
            valid_amounts, test_info, raise_if_none=raise_if_none
        )
        parsed_inv[self.name] = amount

    def _get_amount_untaxed(self, *args):
        return self._get_amount_total(*args)

    def _get_amount_tax(self, *args):
        return self._get_amount_total(*args)

    def _get_invoice_number(self, parsed_inv, raw_text, partner_config, test_info):
        partner = partner_config["recordset"]
        pattern = self.regexp or partner._prepare_simple_pdf_invoice_number_regex()
        test_info[self.name] = {"pattern": pattern}
        restrict_text = self.restrict_text(raw_text, test_info)
        res_regex = regex.findall(pattern, restrict_text)
        test_info[self.name]["res_regex"] = res_regex

        inv_number = self.get_value_from_list(res_regex, test_info, raise_if_none=False)
        if inv_number:
            parsed_inv[self.name] = inv_number.strip()
        else:
            parsed_inv["failed_fields"].append(self.name)

    def _get_description(self, parsed_inv, raw_text, partner_config, test_info):
        self.ensure_one()
        pattern = self.regexp
        test_info[self.name] = {"pattern": pattern}
        restrict_text = self.restrict_text(raw_text, test_info)
        res_regex = regex.findall(pattern, restrict_text)
        test_info[self.name]["res_regex"] = res_regex
        description = self.get_value_from_list(
            res_regex, test_info, raise_if_none=False
        )
        if description:
            parsed_inv[self.name] = description.strip()
        else:
            parsed_inv["failed_fields"].append(self.name)
