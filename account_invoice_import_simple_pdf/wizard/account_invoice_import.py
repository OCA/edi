# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import shutil
import subprocess
from tempfile import NamedTemporaryFile

from odoo import _, api, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)
try:
    import fitz
except ImportError:
    logger.debug("Cannot import PyMuPDF")
try:
    import regex
except ImportError:
    logger.debug("Cannot import regex")
try:
    import pdfplumber
except ImportError:
    logger.debug("Cannot import pdfplumber")
try:
    import pdftotext
except ImportError:
    logger.debug("Cannot import pdftotext")


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def fallback_parse_pdf_invoice(self, file_data):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_bank_statement_import_*
        modules"""
        return self.simple_pdf_parse_invoice(file_data)

    @api.model
    def _simple_pdf_text_extraction_pymupdf(self, fileobj, test_info):
        res = False
        try:
            pages = []
            doc = fitz.open(fileobj.name)
            for page in doc:
                pages.append(page.getText("text"))
            res = {
                "all": "\n\n".join(pages),
                "first": pages and pages[0] or "",
            }
            logger.info("Text extraction made with PyMuPDF")
            test_info["text_extraction"] = "pymupdf"
        except Exception as e:
            logger.warning("Text extraction with PyMuPDF failed. Error: %s", e)
        return res

    @api.model
    def _simple_pdf_text_extraction_pdfplumber(self, fileobj, test_info):
        res = False
        with pdfplumber.open(fileobj.name, laparams={"detect_vertical": True}) as pdf:
            pages = []
            for pdf_page in pdf.pages:
                pages.append(
                    pdf_page.extract_text(
                        layout=True, use_text_flow=True, keep_blank_chars=True
                    )
                )
            res = {
                "all": "\n\n".join(pages),
                "first": pages and pages[0] or "",
            }
        test_info["text_extraction"] = "pdfplumber"
        logger.info("Text extraction made with pdfplumber")
        return res

    @api.model
    def _simple_pdf_pdftotext_cmd_call(self, fileobj, test_info, first_page=False):
        res = False
        if not shutil.which("pdftotext"):
            logger.warning(
                "Could not find the pdftotext utility. Hint: sudo apt install poppler-utils"
            )
            return False
        cmd_args = ["pdftotext"]
        if first_page:
            cmd_args += ["-l", "1"]
        cmd_args += ["-layout", fileobj.name, "-"]
        try:
            out, err = subprocess.Popen(cmd_args, stdout=subprocess.PIPE).communicate()
            if err:
                logger.debug("pdftotext_cmd err=%s", err)
            if out:
                res = out.decode("utf8")
        except Exception as e:
            logger.info("Text extraction with pdftotext command failed. Error: %s", e)
        return res

    @api.model
    def _simple_pdf_text_extraction_pdftotext_cmd(self, fileobj, test_info):
        res_all = self._simple_pdf_pdftotext_cmd_call(fileobj, test_info)
        if not res_all:
            return False
        res = {
            "all": res_all,
            "first": self._simple_pdf_pdftotext_cmd_call(
                fileobj, test_info, first_page=True
            ),
        }
        test_info["text_extraction"] = "pdftotext.cmd"
        logger.info("Text extraction made with pdftotext command")
        return res

    @api.model
    def _simple_pdf_text_extraction_pdftotext_lib(self, fileobj, test_info):
        # pdftotext lib doc: https://github.com/jalan/pdftotext
        res = False
        try:
            with open(fileobj.name, "rb") as pdf_file:
                pdf = pdftotext.PDF(pdf_file)
                res = {
                    "all": "\n\n".join(pdf),
                    "first": pdf[0],
                }
            logger.info("Text extraction made with pdftotext lib")
            test_info["text_extraction"] = "pdftotext.lib"
        except Exception as e:
            logger.warning("Text extraction with pdftotext lib failed. Error: %s", e)
        return res

    @api.model
    def _simple_pdf_text_extraction_specific_tool(
        self, specific_tool, fileobj, test_info
    ):
        res = False
        if specific_tool == "pymupdf":
            res = self._simple_pdf_text_extraction_pymupdf(fileobj, test_info)
        elif specific_tool == "pdftotext.lib":
            res = self._simple_pdf_text_extraction_pdftotext_lib(fileobj, test_info)
        elif specific_tool == "pdftotext.cmd":
            res = self._simple_pdf_text_extraction_pdftotext_cmd(fileobj, test_info)
        elif specific_tool == "pdfplumber":
            res = self._simple_pdf_text_extraction_pdfplumber(fileobj, test_info)
        else:
            raise UserError(
                _(
                    "System Parameter 'invoice_import_simple_pdf.pdf2txt' "
                    "has an invalid value '%s'."
                )
                % specific_tool
            )
        if not res:
            raise UserError(
                _(
                    "Odoo could not extract the text from the PDF invoice "
                    "with the method %s. Refer to the Odoo server logs for more technical "
                    "information about the cause of the failure."
                )
                % specific_tool
            )
        return res

    @api.model
    def simple_pdf_text_extraction(self, file_data, test_info):
        fileobj = NamedTemporaryFile("wb", prefix="odoo-simple-pdf-", suffix=".pdf")
        fileobj.write(file_data)
        # Extract text from PDF
        # Very interesting reading:
        # https://dida.do/blog/how-to-extract-text-from-pdf
        # https://github.com/erfelipe/PDFtextExtraction
        specific_tool = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("invoice_import_simple_pdf.pdf2txt")
        )
        if specific_tool:
            specific_tool = specific_tool.strip().lower()
        test_info["text_extraction_config"] = specific_tool
        if specific_tool:
            res = self._simple_pdf_text_extraction_specific_tool(
                specific_tool, fileobj, test_info
            )
        else:
            # From best tool to worst
            res = self._simple_pdf_text_extraction_pymupdf(fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdftotext_lib(fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdftotext_cmd(fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdfplumber(fileobj, test_info)
            if not res:
                raise UserError(
                    _(
                        "Odoo could not extract the text from the PDF invoice. "
                        "Refer to the Odoo server logs for more technical information "
                        "about the cause of the failure."
                    )
                )
        for key, text in res.items():
            if text:
                # Remove lonely accents
                # example : Free mobile invoices for months with accents
                # i.e. février, août, décembre
                # that are extracted as f´evrier, aoˆut, d´ecembre
                res[key] = regex.sub(test_info["lonely_accents"], "", text)

        res["all_no_space"] = regex.sub(
            "%s+" % test_info["space_pattern"], "", res["all"]
        )
        res["first_no_space"] = regex.sub(
            "%s+" % test_info["space_pattern"], "", res["first"]
        )
        fileobj.close()
        return res

    @api.model
    def simple_pdf_match_partner(self, raw_text_no_space, test_results=None):
        if test_results is None:
            test_results = []
        partner_id = False
        rpo = self.env["res.partner"]
        # Warning: invoices have the VAT number of the supplier, but they often
        # also have the VAT number of the customer (i.e. the VAT number of our company)
        # So we exclude it from the search
        partners = rpo.search_read(
            [
                "|",
                ("vat", "!=", False),
                ("simple_pdf_keyword", "!=", False),
                ("parent_id", "=", False),
                ("is_company", "=", True),
                ("id", "!=", self.env.company.partner_id.id),
            ],
            ["simple_pdf_keyword", "vat"],
        )
        for partner in partners:
            if partner["simple_pdf_keyword"] and partner["simple_pdf_keyword"].strip():
                keywords = partner["simple_pdf_keyword"].replace(" ", "").split("|")
                found_res = [keyword in raw_text_no_space for keyword in keywords]
                if all(found_res):
                    partner_id = partner["id"]
                    result_label = _("Successful match on %d keywords (%s)") % (
                        len(keywords),
                        ", ".join(keywords),
                    )
                    test_results.append("<li>%s</li>" % result_label)
                    break
            elif partner["vat"]:
                if partner["vat"] in raw_text_no_space:
                    partner_id = partner["id"]
                    result_label = (
                        _("Successful match on VAT number '%s'") % partner["vat"]
                    )
                    test_results.append("<li>%s</li>" % result_label)
                    break
        return partner_id

    @api.model
    def _get_space_pattern(self):
        # https://en.wikipedia.org/wiki/Whitespace_character
        # I cannot use \p{White_space} because it includes carriage return
        space_ints = [
            32,
            160,
            8192,
            8193,
            8194,
            8195,
            8196,
            8197,
            8198,
            8199,
            8200,
            8201,
            8202,
            8239,
            8287,
        ]
        return "[%s]" % "".join([chr(x) for x in space_ints])

    @api.model
    def _get_lonely_accents(self):
        lonely_accents = [
            "\u00B4",  # acute accent
            "\u0060",  # grave accent
            "\u005E",  # circumflex accent
            "\u00A8",  # diaeresis
            "\u02CA",  # modifier letter acute accent
            "\u02CB",  # modifier letter grave accent
            "\u02C6",  # modifier letter circumflex accent
        ]
        return "[%s]" % "".join(lonely_accents)

    @api.model
    def _simple_pdf_update_test_info(self, test_info):
        aiispfo = self.env["account.invoice.import.simple.pdf.fields"]
        test_info.update(
            {
                "date_format_sel": dict(
                    aiispfo.fields_get("date_format", "selection")["date_format"][
                        "selection"
                    ]
                ),
                "field_name_sel": dict(
                    aiispfo.fields_get("name", "selection")["name"]["selection"]
                ),
                "extract_rule_sel": dict(
                    aiispfo.fields_get("extract_rule", "selection")["extract_rule"][
                        "selection"
                    ]
                ),
                "space_pattern": self._get_space_pattern(),
                "lonely_accents": self._get_lonely_accents(),
            }
        )

    @api.model
    def simple_pdf_parse_invoice(self, file_data, test_info=None):
        if test_info is None:
            test_info = {"test_mode": False}
        self._simple_pdf_update_test_info(test_info)
        rpo = self.env["res.partner"]
        logger.info("Trying to analyze PDF invoice with simple pdf module")
        raw_text_dict = self.simple_pdf_text_extraction(file_data, test_info)
        partner_id = self.simple_pdf_match_partner(raw_text_dict["all_no_space"])
        if not partner_id:
            raise UserError(_("Simple PDF Import: count not find Vendor."))
        partner = rpo.browse(partner_id)
        raw_text = (
            partner.simple_pdf_pages == "first"
            and raw_text_dict["first"]
            or raw_text_dict["all"]
        )
        logger.info(
            "Simple pdf import found partner %s ID %d", partner.display_name, partner_id
        )
        partner_config = partner._simple_pdf_partner_config()
        parsed_inv = {
            "partner": {"recordset": partner},
            "currency": {"recordset": partner_config["currency"]},
            "failed_fields": [],
            "chatter_msg": [],
        }

        # Check field config
        for field in partner.simple_pdf_field_ids:
            logger.debug("Working on field %s", field.name)
            try:
                getattr(field, "_get_%s" % field.name)(
                    parsed_inv, raw_text, partner_config, test_info
                )
            except AttributeError:
                raise UserError(
                    _("Missing parse method for field '%s'. This should never happen.")
                    % field.name
                )

        failed_fields = parsed_inv.pop("failed_fields")
        if failed_fields:
            parsed_inv["chatter_msg"].append(
                _("<b>Failed</b> to extract the following field(s): %s.")
                % ", ".join(
                    [
                        "<b>%s</b>" % test_info["field_name_sel"][failed_field]
                        for failed_field in failed_fields
                    ]
                )
            )

        logger.info("simple pdf parsed_inv=%s", parsed_inv)
        return parsed_inv
