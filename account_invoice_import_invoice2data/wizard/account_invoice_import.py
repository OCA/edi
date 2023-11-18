# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging
import os
import re
import shutil
from tempfile import NamedTemporaryFile

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_compare

logger = logging.getLogger(__name__)

try:
    from invoice2data.extract.loader import read_templates
    from invoice2data.main import extract_data, logger as loggeri2data
except ImportError:
    logger.debug("Cannot import invoice2data")
try:
    from invoice2data.input import tesseract
except ImportError:
    logger.debug("Cannot import tesseract")


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def fallback_parse_pdf_invoice(self, file_data):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_bank_statement_import_*
        modules"""
        res = super().fallback_parse_pdf_invoice(file_data)
        if not res:
            res = self.invoice2data_parse_invoice(file_data)
        return res

    @api.model
    def parse_invoice2data_taxes(self, line):
        taxes = []
        type_code = "VAT"
        price_include = False
        # CategoryCode assume standard rate s for standard or low rate AA
        categ_code = ""  # AA
        percentage = line.get("line_tax_percent")
        fixed_amount = line.get("line_tax_amount")
        if percentage:
            amount_type = "percent"
            amount = percentage
        elif fixed_amount:
            amount_type = "fixed"
            amount = fixed_amount
        elif line.get("price_total") and not line.get("price_subtotal"):
            price_include = True
        else:
            return taxes
        taxes = [
            {
                "amount_type": amount_type,
                "amount": float(amount),
                "price_include": price_include,
                "unece_type_code": type_code,
                "unece_categ_code": categ_code,
                # "unece_due_date_code": due_date_code,
            }
        ]
        return taxes

    def _clean_string(self, string):
        return re.sub(r"\W+", "", string)

    def _clean_digits(self, string):
        return re.sub(r"\D+", "", string)

    @api.model
    def invoice2data_parse_invoice(self, file_data):
        logger.info("Trying to analyze PDF invoice with invoice2data lib")
        fileobj = NamedTemporaryFile(
            "wb", prefix="odoo-aii-inv2data-pdf-", suffix=".pdf"
        )
        fileobj.write(file_data)
        loggeri2data.setLevel(logger.getEffectiveLevel())
        local_templates_dir = tools.config.get("invoice2data_templates_dir", False)
        logger.debug("invoice2data local_templates_dir=%s", local_templates_dir)
        templates = []
        if local_templates_dir and os.path.isdir(local_templates_dir):
            templates += read_templates(local_templates_dir)
        exclude_built_in_templates = tools.config.get(
            "invoice2data_exclude_built_in_templates", False
        )
        if not exclude_built_in_templates:
            templates += read_templates()
        logger.debug("Calling invoice2data.extract_data with templates=%s", templates)
        try:
            invoice2data_res = extract_data(fileobj.name, templates=templates)
        except Exception as e:
            fileobj.close()
            raise UserError(_("PDF Invoice parsing failed. Error message: %s") % e)
        if not invoice2data_res:
            if not shutil.which("tesseract"):
                logger.warning(
                    "Fallback on tesseract impossible, Could not find the utility. "
                    "Hint: sudo apt install tesseract-ocr"
                )
                fileobj.close()
                return False
            # Fallback on tesseract
            logger.info("PDF Invoice parsing failed: Falling back on Tesseract ocr")
            try:
                # from invoice2data.input import tesseract
                invoice2data_res = extract_data(
                    fileobj.name, templates=templates, input_module=tesseract
                )
            except Exception as e:
                fileobj.close()
                raise UserError(_("PDF Invoice parsing failed. Error message: %s") % e)
            if not invoice2data_res:
                fileobj.close()
                raise UserError(
                    _(
                        "This PDF invoice doesn't match a known template of "
                        "the invoice2data lib."
                    )
                )
        logger.info("Result of invoice2data PDF extraction: %s", invoice2data_res)
        fileobj.close()
        return self.invoice2data_to_parsed_inv(invoice2data_res)

    def invoice2data_prepare_lines(self, lines):
        """Manipulate line data to match with account_invoice_import"""
        for line in lines:
            line["price_unit"] = float(line.get("price_unit", 0))
            taxes = self.parse_invoice2data_taxes(line)
            line["taxes"] = taxes  # or global_taxes,
            product_dict = {
                "barcode": line.get("barcode"),
                "code": line.get("code", line.get("name")),
            }
            line["product"] = product_dict
            if line.get("date_start"):
                line["date_start"] = line.get("date_start")
                line["date_end"] = line.get("date_end")
            if line.get("line_note"):
                line["line_note"] = line.get("line_note")
            line["sectionheader"] = line.get("sectionheader")
            # qty 0 should be allowed to import notes, but not supported by document_import
            line["qty"] = float(line.get("qty", 1))
            if line["qty"] > 0:
                uom_dict = {
                    "unece_code": line.get("unece_code"),
                    "name": line.get("uom"),
                }
                line["uom"] = uom_dict
                line["discount"] = float(line.get("discount", 0.0))
                if line.get("price_subtotal"):
                    line["price_subtotal"] = float(line.get("price_subtotal"))
                if line.get("line_note"):
                    line["line_note"] = line.get("line_note")
                line["sectionheader"] = line.get("sectionheader")
        return lines

    @api.model
    def invoice2data_to_parsed_inv(self, invoice2data_res):
        lines = invoice2data_res.get("lines", [])
        prepared_lines = self.invoice2data_prepare_lines(lines)

        parsed_inv = {
            "partner": {
                "vat": self._clean_string(invoice2data_res.get("vat", "")),
                "name": invoice2data_res.get("partner_name"),
                "street": invoice2data_res.get("partner_street"),
                "street2": invoice2data_res.get("partner_street2"),
                "street3": invoice2data_res.get("partner_street3"),
                "city": invoice2data_res.get("partner_city"),
                "zip": invoice2data_res.get("partner_zip"),
                "country_code": invoice2data_res.get("country_code"),
                "state_code": invoice2data_res.get("state_code"),
                "email": invoice2data_res.get("partner_email"),
                "website": invoice2data_res.get("partner_website"),
                "phone": invoice2data_res.get("telephone"),
                "mobile": invoice2data_res.get("mobile"),
                "ref": invoice2data_res.get("partner_ref"),
                "siren": invoice2data_res.get("siren"),
                "coc_registration_number": self._clean_digits(
                    invoice2data_res.get("partner_coc", "")
                ),
            },
            "bic": self._clean_string(invoice2data_res.get("bic", "")),
            "iban": self._clean_string(invoice2data_res.get("iban", "")),
            "currency": {
                "iso": invoice2data_res.get("currency"),
                "currency_symbol": invoice2data_res.get("currency_symbol"),
                "country_code": invoice2data_res.get("country_code"),
                "iso_or_symbol": invoice2data_res.get("currency"),
            },
            "amount_total": invoice2data_res.get("amount"),
            "date": invoice2data_res.get("date"),
            "date_due": invoice2data_res.get("date_due"),
            "date_start": invoice2data_res.get("date_start"),
            "date_end": invoice2data_res.get("date_end"),
            "note": invoice2data_res.get("note"),
            "narration": invoice2data_res.get("narration"),
            # sale_order_customer_free_ref
            "customer_order_number": invoice2data_res.get("customer_order_number"),
            "customer_order_free_ref": invoice2data_res.get("customer_order_free_ref"),
            "purchase_order_id": invoice2data_res.get("purchase_order_id"),
            "mandate_id": invoice2data_res.get("mandate_id"),
            "payment_reference": invoice2data_res.get("payment_reference"),
            "payment_unece_code": invoice2data_res.get("payment_unece_code"),
            "incoterm": invoice2data_res.get("incoterm"),
            "lines": prepared_lines,
        }
        for field in ["invoice_number", "description"]:
            if isinstance(invoice2data_res.get(field), list):
                parsed_inv[field] = " ".join(invoice2data_res[field])
            else:
                parsed_inv[field] = invoice2data_res.get(field)
        if "amount_untaxed" in invoice2data_res:
            parsed_inv["amount_untaxed"] = invoice2data_res["amount_untaxed"]
        if "amount_tax" in invoice2data_res:
            parsed_inv["amount_tax"] = invoice2data_res["amount_tax"]

            if float_compare(
                parsed_inv["amount_untaxed"],
                parsed_inv["amount_tax"],
                precision_rounding=0.01,
            ):
                logger.warning(prepared_lines)

                # if there are no taxes create tax adjustment lines
                if not any(
                    il["taxes"][0].get("amount", 0.0) > 0
                    for il in prepared_lines
                    if "amount" in ["taxes"]
                ):
                    logger.info(
                        "The total amount is different from the untaxed amount, "
                        "but no tax has been configured !"
                    )

                    tax_lines = invoice2data_res.get("tax_lines", [])
                    logger.warning(tax_lines)

                    tax_correction_lines = [
                        il for il in tax_lines if il.get("line_tax_amount") > 0
                    ]
                    logger.warning(tax_correction_lines)

                    for tcl in tax_correction_lines:
                        tcl["name"] = _("%s VAT Correction") % tcl["line_tax_percent"]
                        tcl["qty"] = 1
                        tcl["price_unit"] = tcl["price_subtotal"]

                    tax_correction_lines = self.invoice2data_prepare_lines(
                        tax_correction_lines
                    )
                    logger.error(tax_correction_lines)

                    parsed_inv["lines"] += tax_correction_lines
                    logger.warning("total invoice lines")
                    logger.warning(parsed_inv["lines"])

        if "company_vat" in invoice2data_res:
            parsed_inv["company"] = {"vat": invoice2data_res["company_vat"]}
        for key, value in parsed_inv.items():
            if key.startswith("date") and isinstance(value, datetime.datetime):
                parsed_inv[key] = fields.Date.to_string(value)
            if key.startswith("amount") and isinstance(value, str):
                parsed_inv[key] = float(value)
        return parsed_inv
