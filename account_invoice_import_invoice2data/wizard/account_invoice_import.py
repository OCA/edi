# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
import shutil
from tempfile import NamedTemporaryFile

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

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

    @api.model
    def invoice2data_to_parsed_inv(self, invoice2data_res):
        lines = invoice2data_res.get("lines", [])

        for line in lines:
            # Manipulate line data to match with account_invoice_import
            line["price_unit"] = float(line.get("price_unit", 0))
            # qty 0 should be allowed to import notes, but nut supported by document_import
            line["qty"] = float(line.get("qty", 1))
            if line["qty"] > 0:
                product_dict = {
                    "barcode": line.get("barcode"),
                    "code": line.get("code", line.get("name")),
                }
                line["product"] = product_dict
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

        parsed_inv = {
            "partner": {
                "vat": invoice2data_res.get("vat"),
                "name": invoice2data_res.get("partner_name"),
                "street": invoice2data_res.get("partner_street"),
                "street2": invoice2data_res.get("partner_street2"),
                "city": invoice2data_res.get("partner_city"),
                "zip": invoice2data_res.get("partner_zip"),
                "country_code": invoice2data_res.get("country_code"),
                "email": invoice2data_res.get("partner_email"),
                "website": invoice2data_res.get("partner_website"),
                "phone": invoice2data_res.get("telephone"),
                "siren": invoice2data_res.get("siren"),
                "coc_registration_number": invoice2data_res.get("partner_coc"),
            },
            "bic": invoice2data_res.get("bic"),
            "iban": invoice2data_res.get("iban"),
            "currency": {
                "iso": invoice2data_res.get("currency"),
            },
            "amount_total": invoice2data_res.get("amount"),
            "date": invoice2data_res.get("date"),
            "date_due": invoice2data_res.get("date_due"),
            "date_start": invoice2data_res.get("date_start"),
            "date_end": invoice2data_res.get("date_end"),
            "note": invoice2data_res.get("note"),
            "lines": lines,
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
        if "company_vat" in invoice2data_res:
            parsed_inv["company"] = {"vat": invoice2data_res["company_vat"]}
        for key, value in parsed_inv.items():
            if key.startswith("date") and value:
                parsed_inv[key] = fields.Date.to_string(value)
        return parsed_inv
