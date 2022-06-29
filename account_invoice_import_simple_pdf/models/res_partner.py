# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_amount, format_date, format_datetime

logger = logging.getLogger(__name__)
ERROR_STYLE = ' style="color:red;"'

try:
    import regex
except ImportError:
    logger.debug("Cannot import regex")


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _simple_pdf_date_format_sel(self):
        return [
            ("dd-mm-y4", _("DD MM YYYY")),
            ("dd-month-y4", _("DD Month YYYY")),
            ("month-dd-y4", _("Month DD YYYY")),
            ("mm-dd-y4", _("MM DD YYYY")),
            ("y4-mm-dd", _("YYYY MM DD")),
            ("dd-mm-y2", _("DD MM YY")),
            ("dd-month-y2", _("DD Month YY")),
            ("month-dd-y2", _("Month DD YY")),
            ("mm-dd-y2", _("MM DD YY")),
        ]

    @api.model
    def _simple_pdf_date_separator_sel(self):
        return [
            ("slash", "/"),
            ("dash", _("dash")),
            ("dot", _("dot")),
            ("space", _("space")),
        ]

    simple_pdf_keyword = fields.Char(
        help="If empty, Odoo will use the VAT number to identify the partner. "
        "To match on several keywords, separate them with '|' (pipe)."
    )
    # Temporary hack: I disable the default values for the fields
    # simple_pdf_date_format and simple_pdf_date_separator
    # to avoid the following bug:
    # https://github.com/odoo/odoo/issues/75492
    simple_pdf_date_format = fields.Selection(
        "_simple_pdf_date_format_sel",
        string="Date Format",
        # default="dd-mm-y4",
        help="If the date format uses 'Month', check that the language is "
        "properly configured on the partner. 'Month' works both in full and "
        "short version ('January' and 'Jan.').",
    )
    simple_pdf_date_separator = fields.Selection(
        "_simple_pdf_date_separator_sel",
        # default="slash",
        string="Date Separator",
        help="If the date looks like 'Sep. 4, 2021', use 'space' as date "
        "separator (Odoo will ignore the dot and comma).",
    )
    simple_pdf_decimal_separator = fields.Selection(
        [
            ("dot", "dot"),
            ("comma", "comma"),
        ],
        string="Decimal Separator",
        help="If empty, Odoo will use the decimal separator configured on "
        "the language of the partner.",
    )
    simple_pdf_thousand_separator = fields.Selection(
        [
            ("none", "none"),
            ("space", "space"),
            ("dot", "dot"),
            ("comma", "comma"),
            ("apostrophe", "apostrophe"),
        ],
        string="Thousand Separator",
        help="If empty, Odoo will use the thousand separator configured on "
        "the language of the partner.",
    )
    simple_pdf_pages = fields.Selection(
        [
            ("first", "First Page Only"),
            ("all", "All Pages"),
        ],
        default="all",
        string="Page Analysis",
    )
    simple_pdf_currency_id = fields.Many2one(
        "res.currency",
        string="Invoice Import Currency",
        ondelete="restrict",
        help="If empty, Odoo will use the company currency.",
    )
    simple_pdf_field_ids = fields.One2many(
        "account.invoice.import.simple.pdf.fields",
        "partner_id",
        string="Fields for PDF Invoice Import",
    )
    simple_pdf_invoice_number_ids = fields.One2many(
        "account.invoice.import.simple.pdf.invoice.number",
        "partner_id",
        string="Invoice Import Number Format",
    )
    simple_pdf_test_file = fields.Binary(
        string="Test PDF Invoice File", attachment=True
    )
    simple_pdf_test_filename = fields.Char(string="Test PDF Invoice Filename")
    simple_pdf_test_raw_text = fields.Text(string="Test Text Extraction", readonly=True)
    simple_pdf_test_results = fields.Html(string="Test Results", readonly=True)

    @api.constrains("simple_pdf_decimal_separator", "simple_pdf_thousand_separator")
    def _check_simple_pdf_separator(self):
        for partner in self:
            if (
                partner.simple_pdf_decimal_separator
                and partner.simple_pdf_decimal_separator
                == partner.simple_pdf_thousand_separator
            ):
                raise ValidationError(
                    _(
                        "For partner '%s', the decimal separator cannot be "
                        "the same as the thousand separator."
                    )
                    % partner.display_name
                )

    @api.onchange("simple_pdf_decimal_separator")
    def simple_pdf_decimal_separator_change(self):
        if (
            self.simple_pdf_decimal_separator == "comma"
            and self.simple_pdf_thousand_separator == "comma"
        ):
            self.simple_pdf_thousand_separator = "dot"

    @api.onchange("simple_pdf_date_format")
    def simple_pdf_date_format_change(self):
        if self.simple_pdf_date_format and "month" in self.simple_pdf_date_format:
            self.simple_pdf_date_separator = "space"

    def _prepare_simple_pdf_invoice_number_regex(self):
        self.ensure_one()
        if not self.simple_pdf_invoice_number_ids:
            raise UserError(
                _("Missing invoice number format configuration on partner '%s'.")
                % self.display_name
            )
        regex = []
        for entry in self.simple_pdf_invoice_number_ids:
            entry._prepare_invoice_number_regex(regex)
        regex_string = "".join(regex)
        return regex_string

    def pdf_simple_generate_default_fields(self):
        self.ensure_one()
        assert not self.parent_id
        assert self.is_company
        assert not self.simple_pdf_field_ids
        def_fields = [
            {"name": "amount_total", "extract_rule": "max"},
            {"name": "amount_untaxed", "extract_rule": "position_end", "position": 3},
            {"name": "invoice_number", "extract_rule": "first"},
            {"name": "date", "extract_rule": "first"},
        ]
        self.write(
            {
                "simple_pdf_field_ids": [(0, 0, field_val) for field_val in def_fields],
            }
        )

    def pdf_simple_test_cleanup(self):
        self.ensure_one()
        self.write(
            {
                "simple_pdf_test_raw_text": False,
                "simple_pdf_test_results": False,
                "simple_pdf_test_filename": False,
                "simple_pdf_test_file": False,
            }
        )

    def pdf_simple_test_run(self):
        self.ensure_one()
        aiio = self.env["account.invoice.import"]
        rpo = self.env["res.partner"]
        vals = {}
        test_results = []
        test_results.append("<small>%s</small><br/>" % _("Errors are in red."))
        test_results.append(
            "<small>%s %s</small><br/>"
            % (_("Test Date:"), format_datetime(self.env, fields.Datetime.now()))
        )
        if not self.simple_pdf_test_file:
            raise UserError(_("You must upload a test PDF invoice."))
        test_info = {"test_mode": True}
        aiio._simple_pdf_update_test_info(test_info)
        file_data = base64.b64decode(self.simple_pdf_test_file)
        raw_text_dict = aiio.simple_pdf_text_extraction(file_data, test_info)
        test_results.append(
            "<small>%s %s</small><br/>"
            % (
                _("Text extraction system parameter:"),
                test_info.get("text_extraction_config") or _("none"),
            )
        )
        test_results.append(
            "<small>%s %s</small><br/>"
            % (_("Text extraction tool used:"), test_info.get("text_extraction"))
        )
        if self.simple_pdf_pages == "first":
            vals["simple_pdf_test_raw_text"] = raw_text_dict["first"]
        else:
            vals["simple_pdf_test_raw_text"] = raw_text_dict["all"]
        test_results.append("<h3>%s</h3><ul>" % _("Searching Partner"))
        partner_id = aiio.simple_pdf_match_partner(
            raw_text_dict["all_no_space"], test_results
        )
        partner_ok = False
        if partner_id:
            partner = rpo.browse(partner_id)
            if partner_id == self.id:
                partner_ok = True
                partner_result = _("Current partner found")
            else:
                partner_result = "%s %s" % (
                    _("Found another partner:"),
                    partner.display_name,
                )
        else:
            partner_result = _("No partner found.")
        test_results.append(
            "<li><b>%s</b> <b%s>%s</b></li></ul>"
            % (_("Result:"), not partner_ok and ERROR_STYLE or "", partner_result)
        )
        if partner_ok:
            partner_config = self._simple_pdf_partner_config()
            test_results.append("<h3>%s</h3><ul>" % _("Amount Setup"))
            test_results.append(
                """<li>%s "%s" (%s)</li>"""
                % (
                    _("Decimal Separator:"),
                    partner_config["decimal_sep"],
                    partner_config["char2separator"].get(
                        partner_config["decimal_sep"], _("unknown")
                    ),
                )
            )
            test_results.append(
                """<li>%s "%s" (%s)</li></ul>"""
                % (
                    _("Thousand Separator:"),
                    partner_config["thousand_sep"],
                    partner_config["char2separator"].get(
                        partner_config["thousand_sep"], _("unknown")
                    ),
                )
            )
            parsed_inv = aiio.simple_pdf_parse_invoice(file_data, test_info)
            key2label = {
                "pattern": _("Regular Expression"),
                "date_format": _("Date Format"),
                "res_regex": _("Raw List"),
                "valid_list": _("Valid-data Filtered List"),
                "sorted_list": _("Ordered List"),
                "error_msg": _("Error message"),
                "start": _("Start String"),
                "end": _("End String"),
            }
            for field in self.simple_pdf_field_ids:
                test_results.append(
                    "<h3>%s</h3><ul>" % test_info["field_name_sel"][field.name]
                )
                extract_method = test_info["extract_rule_sel"][field.extract_rule]
                if field.extract_rule.startswith("position_"):
                    extract_method += _(", Position: %d") % field.position
                test_results.append(
                    "<li>%s %s</li>" % (_("Extract Rule:"), extract_method)
                )
                for key, value in test_info[field.name].items():
                    if key != "pattern" or self.env.user.has_group("base.group_system"):
                        test_results.append("<li>%s: %s</li>" % (key2label[key], value))

                result = parsed_inv.get(field.name)
                if "date" in field.name and result:
                    result = format_date(self.env, result)
                if "amount" in field.name and result:
                    result = format_amount(
                        self.env, result, parsed_inv["currency"]["recordset"]
                    )
                test_results.append(
                    "<li><b>%s</b> <b%s>%s</b></li></ul>"
                    % (
                        _("Result:"),
                        not result and ERROR_STYLE or "",
                        result or _("None"),
                    )
                )
        vals["simple_pdf_test_results"] = "\n".join(test_results)
        self.write(vals)

    def _simple_pdf_partner_config(self):
        self.ensure_one()
        separator2char = {
            "slash": "/",
            "dash": "-",
            "dot": ".",
            "comma": ",",
            "space": chr(32),  # regular space
            "apostrophe": "'",
            "none": "",
        }
        char2separator = {val: key for key, val in separator2char.items()}
        date_format2regex = {
            "dd": r"\d{1,2}",  # We have to match on July 4, 2021
            "mm": r"\d{1,2}",
            "y4": r"\d{4}",
            "y2": r"\d{2}",
            "month": r"[\p{L}\p{Mn}]{3,15}\.?",
            # \p{L} : any unicode letter (but not digit)
            # \p{Mn} : non spacing mark, for example \u0301 combining acute accent
            # option dot for short month (e.g. 'feb.')
        }
        date_format2dt = {
            "dd": "%d",
            "mm": "%m",
            "month": "%B",
            "y4": "%Y",
            "y2": "%y",
        }
        lang = False
        if self.lang:
            lang = self.env["res.lang"].search([("code", "=", self.lang)], limit=1)
        if self.simple_pdf_decimal_separator:
            decimal_sep = separator2char[self.simple_pdf_decimal_separator]
        elif lang:
            decimal_sep = lang.decimal_point
        else:
            raise UserError(
                _(
                    "Could not get the decimal separator for partner '%s': "
                    "the fields 'Language' and 'Decimal Separator' are "
                    "both empty for this partner."
                )
                % self.display_name
            )
        if self.simple_pdf_thousand_separator:
            thousand_sep = separator2char[self.simple_pdf_thousand_separator]
        elif lang:
            thousand_sep = lang.thousands_sep
            # Remplace all white space characters (no-break-space, narrow no-break-space)
            # by regular space
            if regex.match(r"^\s$", thousand_sep):
                thousand_sep = chr(32)  # regular space
        else:
            thousand_sep = ""
        logger.debug("decimal_sep=|%s| thousand_sep=|%s|", decimal_sep, thousand_sep)
        partner_config = {
            "recordset": self,
            "display_name": self.display_name,
            "date_format": self.simple_pdf_date_format,
            "date_separator": self.simple_pdf_date_separator,
            "currency": self.simple_pdf_currency_id or self.env.company.currency_id,
            "decimal_sep": decimal_sep,
            "thousand_sep": thousand_sep,
            "separator2char": separator2char,
            "char2separator": char2separator,
            "date_format2regex": date_format2regex,
            "date_format2dt": date_format2dt,
            "lang_short": self.lang and self.lang[:2] or None,
        }
        # Check field list
        field_list = [field.name for field in self.simple_pdf_field_ids]
        amount_total_count = field_list.count("amount_total")
        amount_untaxed_count = field_list.count("amount_untaxed")
        amount_tax = field_list.count("amount_tax")
        amount_fields_count = amount_total_count + amount_untaxed_count + amount_tax
        if "date" not in field_list:
            raise UserError(
                _(
                    "You must configure a field extraction rule for "
                    "field 'Date' for partner '%s'."
                )
                % self.display_name
            )
        if amount_fields_count == 0:
            raise UserError(
                _("There is no amount field configured for partner '%s'.")
                % self.display_name
            )
        if amount_fields_count == 1 and amount_total_count == 0:
            raise UserError(
                _(
                    "For partner '%s', only one amount field is configured "
                    "but it is not 'Amount Total'."
                )
                % self.display_name
            )
        return partner_config
