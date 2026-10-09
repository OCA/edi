# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# Copyright 2020-2021 Therp BV (https://therp.nl)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import html
import logging
import mimetypes
from collections import defaultdict
from email.utils import parseaddr
from io import BytesIO
from textwrap import shorten

from babel import Locale
from lxml import etree
from markupsafe import Markup
from stdnum.iban import is_valid as iban_is_valid

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_is_zero, float_round
from odoo.tools.misc import format_amount, formatLang

from odoo.addons.base.models.res_bank import sanitize_account_number

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except (OSError, ImportError) as err:
    logger.debug("Cannot import pypdf. Error details below.")
    logger.debug(err)
try:
    from facturx import (
        get_data_dict_copy_for_logs,
        is_credit_note,
        parse_ubl_cii_xml,
        untdid_get_label,
    )
except (OSError, ImportError) as err:
    logger.debug("Cannot import factur-x. Error details below.")
    logger.debug(err)


class AccountInvoiceImport(models.TransientModel):
    _name = "account.invoice.import"
    _inherit = ["mail.thread"]
    # inherit mail.thread to allow import by mail gateway using message_new()
    _description = "Wizard to import supplier invoices/refunds"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    invoice_attachment_ids = fields.Many2many(
        "ir.attachment", string="PDF or XML Invoices to Import", required=True
    )
    debug_disable_company_check = fields.Boolean(
        string="Disable Company Check",
        help="If enabled, it will disable the check that the buyer "
        "company correspond to the company of the wizard. "
        "It is useful for debug purposes to test the import of a vendor bill "
        "in a test database.",
    )
    show_debug_disable_company_check = fields.Boolean(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        running_env = config.get("running_env")
        if running_env in ("test", "dev"):
            res["show_debug_disable_company_check"] = True
        return res

    @api.model
    def parse_xml_invoice(self, xml_root, import_config):
        self._update_import_config(import_config)
        parsed_inv = False
        try:
            parsed_inv = parse_ubl_cii_xml(
                xml_root, float_as="float", date_as="date", bytes_as="bytes"
            )
        except Exception as err:
            logger.info(
                f"The factur-x lib wasn't able to parse this XML file. Error: {err}"
            )
        return parsed_inv

    @api.model
    def parse_pdf_invoice(self, file_data, import_config):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_statement_import_*
        modules"""
        self._update_import_config(import_config)
        pdf_reader = PdfReader(BytesIO(file_data))
        for attach_obj in pdf_reader.attachment_list:
            filename = attach_obj.name
            logger.info("Attachment '%s' found in PDF", filename)
            mime_res = mimetypes.guess_type(filename)
            if (
                mime_res
                and mime_res[0] in ["application/xml", "text/xml"]
                and attach_obj.content
            ):
                try:
                    xml_root = etree.fromstring(attach_obj.content)
                except Exception as err:
                    logger.warning(
                        "Attachment '%s' is not a valid XML file. Error: %s",
                        filename,
                        err,
                    )
                    continue
                logger.info("Start to parse XML file %s", filename)
                parsed_inv = self.parse_xml_invoice(xml_root, import_config)
                if parsed_inv:
                    return parsed_inv
        parsed_inv = self.fallback_parse_pdf_invoice(file_data, import_config)
        if not parsed_inv:
            parsed_inv = {}
        self._fallback_update_parsed_inv(parsed_inv, import_config)
        # In the fallback scenario, we may have amount_tax and amount_untaxed
        # but not amount total
        return parsed_inv

    def fallback_parse_pdf_invoice(self, file_data, import_config):
        """Designed to be inherited by the module
        account_invoice_import_invoice2data, to be sure the invoice2data
        technique is used after the electronic invoice modules such as
        account_invoice_import_facturx and account_invoice_import_ubl
        """
        self._update_import_config(import_config)
        return False

    def _fallback_update_parsed_inv(self, parsed_inv, import_config):
        if "BT-112" not in parsed_inv:
            # Designed to allow the import of an empty invoice with
            # 1 invoice line at 0 that has the right account/product/analytic
            parsed_inv["BT-112"] = 0
        if "BT-110" in parsed_inv and "BT-109" not in parsed_inv:
            parsed_inv["BT-109"] = parsed_inv["BT-112"] - parsed_inv["BT-110"]
        elif "BT-109" not in parsed_inv and "BT-110" not in parsed_inv:
            # For invoices that never have taxes
            parsed_inv["BT-109"] = parsed_inv["BT-112"]

    @api.model
    def _prepare_create_invoice_no_partner(self, parsed_inv, import_config, vals):
        if import_config.get("email_from"):
            vals["invoice_source_email"] = import_config["email_from"]
        partner_dict = self._get_partner_dict(parsed_inv, import_config)
        if partner_dict:
            if not vals.get("invoice_source_email"):
                for contact_dict in partner_dict.get("contacts") or []:
                    if contact_dict.get("email"):
                        source_email = contact_dict["email"]
                        if partner_dict.get("name"):
                            source_email = f"{partner_dict['name']} <{source_email}>"
                        vals["invoice_source_email"] = source_email
                        break
            partner_data = {
                "is_company": True,
                "country_id": False,
                "state_id": False,
            }
            if import_config["invoice_type"] == "in":
                partner_data["supplier_rank"] = 1
            else:
                partner_data["customer_rank"] = 1
            if (
                partner_dict.get("country_code")
                and partner_dict["country_code"]
                in import_config["speedy"]["country_code2id"]
            ):
                partner_data["country_id"] = import_config["speedy"]["country_code2id"][
                    partner_dict["country_code"]
                ]
                # There are already warnings when country code doesn't exist
                lang = self._get_lang_from_country_code(
                    partner_dict["country_code"], import_config
                )
                if lang:
                    partner_data["lang"] = lang
            if partner_data.get("country_id") and partner_dict.get(
                "country_subdivision"
            ):
                state_ids = list(
                    self.env["res.country.state"]._search(
                        [
                            (
                                "name",
                                "=",
                                partner_dict["country_subdivision"],
                            ),
                            ("country_id", "=", partner_data["country_id"]),
                        ],
                        ["id"],
                        limit=1,
                    )
                )
                if state_ids:
                    partner_data["state_id"] = state_ids[0]
            rpo = self.env["res.partner"]
            # if purchase module is installed
            if (
                import_config["invoice_type"] == "in"
                and hasattr(rpo, "property_purchase_currency_id")
                and parsed_inv["BT-5"] in import_config["speedy"]["currency_code2id"]
            ):
                partner_data["property_purchase_currency_id"] = import_config["speedy"][
                    "currency_code2id"
                ][parsed_inv["BT-5"]]

            partner_dict_key2odoo_field = {
                "name": "name",
                "addr_l1": "street",
                "addr_l2": "street2",
                "addr_l3": "street3",
                "postcode": "zip",
                "city": "city",
                "vat_identifier": "vat",
            }
            for partner_dict_key, odoo_field in partner_dict_key2odoo_field.items():
                value = partner_dict.get(partner_dict_key)
                if value and isinstance(value, str) and hasattr(rpo, odoo_field):
                    partner_data[odoo_field] = value
            vals["import_partner_data"] = partner_data

    @api.model
    def _get_forced_journal_id(self, parsed_inv, import_config, vals):
        forced_journal_id = False
        if import_config["invoice_type"] == "in" and import_config.get(
            "purchase_journal"
        ):
            if import_config["purchase_journal"].type != "purchase":
                msg = (
                    f"Forced purchase journal "
                    f"{import_config['purchase_journal'].display_name} is "
                    f"in fact a {import_config['purchase_journal'].type} journal"
                )
                self._warning_log(import_config, msg)
            elif (
                import_config["purchase_journal"].company_id != import_config["company"]
            ):
                msg = (
                    f"Forced purchase journal "
                    f"{import_config['purchase_journal'].display_name} belongs to "
                    "company "
                    f"{import_config['purchase_journal'].company_id.display_name} "
                    "whereas invoice import is in company "
                    f"{import_config['company'].display_name}"
                )
                self._warning_log(import_config, msg)
            else:
                forced_journal_id = import_config["purchase_journal"].id
        elif import_config["invoice_type"] == "out" and import_config.get(
            "sale_journal"
        ):
            if import_config["sale_journal"].type != "sale":
                msg = (
                    f"Forced sale journal "
                    f"{import_config['sale_journal'].display_name} is in fact "
                    f"a {import_config['sale_journal'].type} journal"
                )
                self._warning_log(import_config, msg)
            elif import_config["sale_journal"].company_id != import_config["company"]:
                msg = (
                    f"Forced sale journal "
                    f"{import_config['sale_journal'].display_name} belongs to company "
                    f"{import_config['sale_journal'].company_id.display_name} whereas "
                    "invoice import is in company "
                    "{import_config['company'].display_name}"
                )
                self._warning_log(import_config, msg)
            else:
                forced_journal_id = import_config["sale_journal"].id
        return forced_journal_id

    @api.model
    def _prepare_create_invoice_vals(self, parsed_inv, import_config):
        company = import_config["company"]
        refund = False
        if parsed_inv.get("BT-3"):
            refund = is_credit_note(parsed_inv)
        vals = {
            "company_id": company.id,
            "invoice_origin": import_config.get("origin"),
            "invoice_date": parsed_inv.get("BT-2"),
            "invoice_line_ids": [],
            "currency_id": import_config["invoice_currency"].id,
        }
        if import_config["invoice_type"] == "in":
            vals["move_type"] = refund and "in_refund" or "in_invoice"
            vals["ref"] = parsed_inv.get("BT-1")
        else:
            vals["move_type"] = refund and "out_refund" or "out_invoice"
            if parsed_inv.get("BT-1"):
                vals["name"] = parsed_inv["BT-1"]
        partner = import_config.get("partner")
        cpartner = import_config.get("commercial_partner")
        if partner:
            vals["partner_id"] = partner.id
            wire_transfer_codes = ("30", "42", "52", "58")
            out_pay_method_line = cpartner.property_outbound_payment_method_line_id
            if (
                parsed_inv.get("BT-81")
                and parsed_inv["BT-81"] in wire_transfer_codes
                and parsed_inv.get("BT-84")
                and vals["move_type"] == "in_invoice"
                and out_pay_method_line
                and out_pay_method_line.payment_method_id.unece_code
                in wire_transfer_codes
            ):
                partner_bank = self._match_bank_account(
                    cpartner,
                    parsed_inv,
                    import_config,
                )
                if partner_bank:
                    vals["partner_bank_id"] = partner_bank.id
        else:
            self._prepare_create_invoice_no_partner(parsed_inv, import_config, vals)
        forced_journal_id = self._get_forced_journal_id(parsed_inv, import_config, vals)
        if forced_journal_id:
            vals["journal_id"] = forced_journal_id
        # Force due date of the invoice
        if parsed_inv.get("BT-9"):
            vals["invoice_date_due"] = parsed_inv["BT-9"]
            # Set invoice_payment_term_id to False because the due date is
            # set by invoice_date + invoice_payment_term_id otherwise
            vals["invoice_payment_term_id"] = False
        # invoice lines
        if parsed_inv.get("BG-25") and not import_config.get("shrink_lines"):
            for line_dict in parsed_inv["BG-25"]:
                lvals = self._prepare_line_vals_bg25(
                    line_dict, parsed_inv, import_config, vals
                )
                vals["invoice_line_ids"].append(Command.create(lvals))
                if lvals["discount"] is None:
                    bg27_line = 0
                    for allowance_dict in line_dict.get("BG-27") or []:
                        bg27_line += 1
                        alvals = self._prepare_line_vals_bg27(
                            bg27_line,
                            allowance_dict,
                            parsed_inv,
                            import_config,
                            lvals,
                        )
                        vals["invoice_line_ids"].append(Command.create(alvals))
                bg28_line = 0
                for charge_dict in line_dict.get("BG-28") or []:
                    bg28_line += 1
                    clvals = self._prepare_line_vals_bg28(
                        bg28_line, charge_dict, parsed_inv, import_config, lvals
                    )
                    vals["invoice_line_ids"].append(Command.create(clvals))
            # BG-20 = global allowances / BG-21 = global charges
            bg20_line = 0
            for allowance_dict in parsed_inv.get("BG-20") or []:
                bg20_line += 1
                lvals = self._prepare_line_vals_bg20(
                    f"BG-20-{bg20_line}",
                    allowance_dict,
                    parsed_inv,
                    import_config,
                    vals,
                )
                vals["invoice_line_ids"].append(Command.create(lvals))
            bg21_line = 0
            for charge_dict in parsed_inv.get("BG-21") or []:
                bg21_line += 1
                lvals = self._prepare_line_vals_bg21(
                    f"BG-21-{bg21_line}",
                    charge_dict,
                    parsed_inv,
                    import_config,
                    vals,
                )
                vals["invoice_line_ids"].append(Command.create(lvals))
        elif (
            parsed_inv.get("BG-23")
            and import_config.get("shrink_lines") == "per_vat_rate"
        ):
            line_nr = 0
            for vatline_dict in parsed_inv["BG-23"]:
                line_nr += 1
                lvals = self._prepare_line_vals_bg23(
                    str(line_nr), vatline_dict, parsed_inv, import_config, vals
                )
                vals["invoice_line_ids"].append(Command.create(lvals))
        else:
            lvals = self._prepare_line_vals_single(parsed_inv, import_config, vals)
            vals["invoice_line_ids"].append(Command.create(lvals))
        # if module account_invoice_check_total from OCA/account-invoicing is installed
        # Maybe we should depend on this module... ? Or have the equivalent
        # that we only "enable" when importing an e-invoice ?
        attachment_ids = []
        for attach_dict in parsed_inv.get("BG-24") or []:
            if attach_dict.get("BT-125") and attach_dict.get("BT-125-2"):
                attachment_ids.append(
                    Command.create(
                        {
                            "raw": attach_dict["BT-125"],
                            "name": attach_dict["BT-125-2"],
                            "res_model": "account.move",
                        }
                    )
                )
        if import_config.get("filename") and import_config.get("file_bin"):
            attachment_ids.append(
                Command.create(
                    {
                        "raw": import_config["file_bin"],
                        "name": import_config["filename"],
                        "res_model": "account.move",
                    }
                )
            )
        if attachment_ids:
            vals["attachment_ids"] = attachment_ids
        narration_list = []
        for note_dict in parsed_inv.get("BG-1") or []:
            if note_dict.get("BT-22"):
                note = False
                if note_dict.get("BT-21"):
                    note_categ = untdid_get_label("4451", note_dict["BT-21"])
                    if note_categ:
                        note = (
                            f"<li><strong>{note_categ}</strong> : "
                            f"{note_dict['BT-22']}</li>"
                        )
                if not note:
                    note = f"<li>{note_dict['BT-22']}</li>"
                narration_list.append(note)
        if narration_list:
            narration = f"<ul>{'\n'.join(narration_list)}</ul>"
            if import_config["invoice_type"] == "in":
                label = self.env._("Notes extracted from the electronic invoice:")
                narration = f"<p>{label}</p>{narration}"
            vals["narration"] = narration
        if hasattr(self.env["account.move"], "check_total"):
            vals["check_total"] = parsed_inv["BT-112"]
        vals["import_warnings"] = self._prepare_import_warnings(import_config)
        if import_config.get("invoice_extra_vals") and isinstance(
            import_config["invoice_extra_vals"], dict
        ):
            vals.update(import_config["invoice_extra_vals"])
        return vals

    def _prepare_import_warnings(self, import_config):
        import_warnings = False
        if import_config["line_warnings"]:
            for line_ref, msg_list in import_config["line_warnings"].items():
                msg = f"<ul>{''.join([f'<li>{msg}</li>' for msg in msg_list])}</ul>"
                line_prefix = self.env._("Invoice Line External ID:")
                import_config["global_warnings"].append(
                    f"{line_prefix} <strong>{line_ref}</strong> {msg}"
                )
        if import_config["global_warnings"]:
            title = self.env._("Electronic invoice import warnings:")
            warning_lis = "".join(
                [f"<li>{x}</li>" for x in import_config["global_warnings"]]
            )
            import_warnings = f"<p><strong>{title}</strong></p><ul>{warning_lis}</ul>"
        return import_warnings and Markup(import_warnings)

    @api.model
    def _prepare_line_vals_shrink_common(self, parsed_inv, import_config, vals):
        product = import_config.get("product")
        lvals = {
            "display_type": "product",
            "quantity": 1,
            "product_id": product and product.id or False,
        }
        self._prepare_line_set_account(lvals, product, import_config)
        if import_config.get("label"):
            lvals["name"] = import_config["label"]
        elif parsed_inv.get("BT-11-0"):
            lvals["name"] = parsed_inv["BT-11-0"]
        # For the moment, we only take into account the 'price_include'
        # option of the first tax
        self._prepare_line_set_global_start_end_dates(lvals, parsed_inv, import_config)
        return lvals

    @api.model
    def _prepare_line_vals_single(self, parsed_inv, import_config, vals):
        cpartner = import_config.get("commercial_partner")  # can be None
        lvals = self._prepare_line_vals_shrink_common(parsed_inv, import_config, vals)
        # For the moment, we only take into account the 'price_include'
        # option of the first tax
        taxes = self.env["account.tax"]
        if import_config.get("product"):
            product = import_config["product"]
            if import_config["invoice_type"] == "out":
                product_taxes = product.taxes_id
            else:
                product_taxes = product.supplier_taxes_id
            taxes = product_taxes.filtered(
                lambda tax: tax.company_id == import_config["company"]
            )
        else:
            taxes = import_config.get("taxes")
        fp = cpartner and cpartner.property_account_position_id or False
        if fp and taxes:
            taxes = fp.map_tax(taxes)
        if taxes:
            lvals["tax_ids"] = [Command.set(taxes.ids)]
        if taxes and taxes[0].price_include:
            lvals["price_unit"] = parsed_inv["BT-112"]
        else:
            lvals["price_unit"] = parsed_inv.get("BT-109")
        return lvals

    @api.model
    def _prepare_line_vals_bg23(
        self, line_nr, vatline_dict, parsed_inv, import_config, vals
    ):
        lvals = self._prepare_line_vals_shrink_common(parsed_inv, import_config, vals)
        taxes = self.env["account.tax"]
        taxes = self._match_vat_tax_bg23(
            line_nr,
            vatline_dict,
            parsed_inv,
            import_config,
        )
        lvals.update(
            {
                "tax_ids": [Command.set(taxes and taxes.ids or [])],
                "price_unit": vatline_dict.get("BT-116"),
                "import_invoice_line_identifier": line_nr,
            }
        )
        return lvals

    @api.model
    def _prepare_line_set_account(self, lvals, product, import_config):
        # product can have a value or not
        # fallback on import_config["product"] has already been made
        # We don't update lvals when there is no account, so that the compute
        # method will set a default value for the account
        account = False
        if product:
            product = product.with_company(import_config["company"].id)
            if import_config["invoice_type"] == "out":
                account = product._get_product_accounts()["income"]
            else:
                account = product._get_product_accounts()["expense"]
        elif import_config.get("account"):
            account = import_config["account"]
        if account:
            cpartner = import_config.get(
                "commercial_partner"
            )  # already has with_company
            if cpartner:
                fp = cpartner and cpartner.property_account_position_id or False
                if fp:
                    account = fp.map_account(account)
            lvals["account_id"] = account.id

    @api.model
    def _prepare_line_set_global_start_end_dates(
        self, lvals, parsed_inv, import_config
    ):
        # We only set global start/end dates if it hasn't already been set at line-level
        if import_config["start_end_dates_installed"]:
            if (
                not lvals.get("start_date")
                and not lvals.get("end_date")
                and parsed_inv.get("BT-73")
                and parsed_inv.get("BT-74")
            ):
                lvals["start_date"] = parsed_inv["BT-73"]
                lvals["end_date"] = parsed_inv["BT-74"]

    @api.model
    def _prepare_line_vals_bg25(self, line_dict, parsed_inv, import_config, vals):
        line_ident = line_dict["BT-126"]
        product = self._match_product(line_dict, parsed_inv, import_config)
        if not product and import_config.get("product"):
            product = import_config["product"]

        partner = import_config.get("commercial_partner")
        if product and import_config["invoice_type"] == "out":
            taxes = product.taxes_id.filtered(
                lambda tax: tax.company_id == import_config["company"]
            )
            # TODO replace by tax_include equivalent ?
            fp = partner and partner.property_account_position_id or False
            if fp and taxes:
                taxes = fp.map_tax(taxes)
        else:
            taxes = self._match_vat_tax_bg25(
                line_dict,
                parsed_inv,
                import_config,
            )
        uom = self._match_uom(line_dict, parsed_inv, import_config)

        if uom and product and product.uom_id.category_id != uom.category_id:
            import_config["line_warnings"][line_ident].append(
                self.env._(
                    "Matched unit of measure (UoM) is "
                    "<strong>%(matched_uom)s</strong>, "
                    "but this UoM doesn't belong to the same category as UoM "
                    "<strong>%(product_uom)s</strong> configured on product "
                    "<em>%(product)s</em>. So Odoo has set the UoM of the product "
                    "(%(product_uom)s).",
                    matched_uom=uom.display_name,
                    product_uom=product.uom_id.display_name,
                    product=product.display_name,
                )
            )
            uom = product.uom_id

        if not uom:
            if product:
                uom = product.uom_id
            else:
                uom = self.env.ref("uom.product_uom_unit")
        price_unit = line_dict["BT-146"]
        if line_dict.get("BT-149"):
            price_unit /= line_dict["BT-149"]
        # Special treatment for single line-level allowance with a percent
        discount = None
        if len(line_dict.get("BG-27", [])) == 1 and line_dict["BG-27"][0].get("rate"):
            discount = line_dict["BG-27"][0]["rate"]
            allowance_base = line_dict["BG-27"][0].get("base_amount")
            if allowance_base:
                line_base = line_dict["BT-129"] * price_unit
                if import_config["invoice_currency"].compare_amounts(
                    allowance_base, line_base
                ):
                    discount = None
        lvals = {
            "display_type": "product",
            "import_invoice_line_identifier": line_ident,
            "product_id": product and product.id or False,
            "product_uom_id": uom.id,
            "quantity": line_dict["BT-129"],
            "price_unit": price_unit,
            # TODO add support for tax incl ?
            "discount": discount,
            "tax_ids": [Command.set(taxes and taxes.ids or [])],
        }
        # to let the compute methods do their work for the default value
        self._prepare_line_set_account(lvals, product, import_config)
        if import_config.get("label"):
            lvals["name"] = import_config["label"]
        else:
            name_list = [line_dict.get("BT-153"), line_dict.get("BT-154")]
            lvals["name"] = "\n".join([x for x in name_list if x])
        if (
            import_config["start_end_dates_installed"]
            and line_dict.get("BT-134")
            and line_dict.get("BT-135")
        ):
            lvals["start_date"] = line_dict["BT-134"]
            lvals["end_date"] = line_dict["BT-135"]
        self._prepare_line_set_global_start_end_dates(lvals, parsed_inv, import_config)
        return lvals

    def _prepare_line_vals_bg27(
        self, bg27_line, allowance_dict, parsed_inv, import_config, lvals
    ):
        allowance_vals = dict(lvals)
        untdid = "5189"
        line_ident = f"{lvals['import_invoice_line_identifier']}-BG27-{bg27_line}"
        allowance_vals.update(
            {
                "import_invoice_line_identifier": line_ident,
                "name": self.env._(
                    "Allowance on %s", shorten(lvals.get("name", ""), 50)
                ),
                "price_unit": allowance_dict["amount"] * -1,
            }
        )
        self._prepare_line_common_bg27_bg28(
            allowance_dict, untdid, parsed_inv, import_config, allowance_vals
        )
        return allowance_vals

    def _prepare_line_vals_bg28(
        self, bg28_line, charge_dict, parsed_inv, import_config, lvals
    ):
        charge_vals = dict(lvals)  # copies product, account, taxes, ...
        untdid = "7161"
        line_ident = f"{lvals['import_invoice_line_identifier']}-BG28-{bg28_line}"
        charge_vals.update(
            {
                "import_invoice_line_identifier": line_ident,
                "name": self.env._(
                    "Extra charge on %s", shorten(lvals.get("name", ""), 50)
                ),
                "price_unit": charge_dict["amount"],
            }
        )
        self._prepare_line_common_bg27_bg28(
            charge_dict, untdid, parsed_inv, import_config, charge_vals
        )
        return charge_vals

    def _prepare_line_common_bg27_bg28(
        self, common_dict, untdid, parsed_inv, import_config, common_vals
    ):
        name_list = [common_vals["name"]]
        untdid_5153_code2label = import_config["speedy"]["untdid_5153_code2label"]
        if common_dict.get("reason"):
            name_list.append(self.env._("Reason: %s", common_dict["reason"]))
        if common_dict.get("reason_code"):
            reason_code_label = untdid_get_label(untdid, common_dict["reason_code"])
            if reason_code_label:
                name_list.append(self.env._("Coded reason: %s", reason_code_label))
            else:
                name_list.append(
                    self.env._(
                        "Unknown reason code '%(code)s' (not in UNTDID %(untdid)s)",
                        code=common_dict["reason_code"],
                        untdid=untdid,
                    )
                )
        elif common_dict.get("non_vat_tax_code"):
            if common_dict["non_vat_tax_code"] in untdid_5153_code2label:
                name_list.append(
                    self.env._(
                        "Reason: Non-VAT Tax '%s'",
                        untdid_5153_code2label[common_dict["non_vat_tax_code"]],
                    )
                )
            else:
                name_list.append(
                    self.env._(
                        "Reason: Non-VAT Tax with code '%s' (not in UNTDID 5153)",
                        common_dict["non_vat_tax_code"],
                    )
                )
        name_last_line = []
        if common_dict.get("base_amount"):
            base_fmt = format_amount(
                self.env, common_dict["base_amount"], import_config["invoice_currency"]
            )
            name_last_line.append(self.env._("Base: %s", base_fmt))
        if common_dict.get("rate"):
            rate_fmt = formatLang(self.env, common_dict["rate"], digits=2)
            name_last_line.append(self.env._("Rate: %s %%", rate_fmt))
        if name_last_line:
            name_list.append(" - ".join(name_last_line))

        common_vals.update(
            {
                "quantity": 1,
                "discount": None,
                "name": "\n".join(name_list),
            }
        )

    def _prepare_line_vals_bg20(
        self, line_ident, allowance_dict, parsed_inv, import_config, vals
    ):
        reason_code_label = untdid_get_label("5189", allowance_dict.get("reason_code"))
        allowance_dict.update(
            {
                "reason_code_label": reason_code_label,
                "amount_signed": allowance_dict["amount"] * -1,
                "untdid": "5189",
                "line_ident": line_ident,
            }
        )
        return self._prepare_line_vals_common_bg20_bg21(
            allowance_dict, parsed_inv, import_config, vals
        )

    def _prepare_line_vals_bg21(
        self, line_ident, charge_dict, parsed_inv, import_config, vals
    ):
        reason_code_label = untdid_get_label("7161", charge_dict.get("reason_code"))
        charge_dict.update(
            {
                "reason_code_label": reason_code_label,
                "amount_signed": charge_dict["amount"],
                "untdid": "7161",
                "line_ident": line_ident,
            }
        )
        return self._prepare_line_vals_common_bg20_bg21(
            charge_dict, parsed_inv, import_config, vals
        )

    def _prepare_line_vals_common_bg20_bg21(
        self, common_dict, parsed_inv, import_config, vals
    ):
        name_list = []
        if common_dict.get("reason"):
            name_list.append(common_dict["reason"])
        if common_dict["reason_code_label"]:
            name_list.append(
                self.env._("Coded reason: %s", common_dict["reason_code_label"])
            )
        elif common_dict.get("reason_code"):
            name_list.append(
                self.env._(
                    "Unknown reason code '%(code)s' (not in UNTDID %(untdid)s)",
                    code=common_dict["reason_code"],
                    untdid=common_dict["untdid"],
                )
            )
        name_last_line = []
        if common_dict.get("base_amount"):
            base_fmt = format_amount(
                self.env, common_dict["base_amount"], import_config["invoice_currency"]
            )
            name_last_line.append(self.env._("Base: %s", base_fmt))
        if common_dict.get("rate"):
            rate_fmt = formatLang(self.env, common_dict["rate"], digits=2)
            name_last_line.append(self.env._("Rate: %s %%", rate_fmt))
        if name_last_line:
            name_list.append(" - ".join(name_last_line))
        vat_tax = self._match_vat_tax_common(
            common_dict["line_ident"],
            common_dict["vat_category_code"],
            int(round(common_dict.get("vat_rate", 0) * 100)),
            parsed_inv,
            import_config,
        )
        product = import_config.get("product")
        lvals = {
            "display_type": "product",
            "product_id": product and product.id or False,
            "name": "\n".join(name_list),
            "quantity": 1,
            "price_unit": common_dict["amount_signed"],
            "import_invoice_line_identifier": common_dict["line_ident"],
            "tax_ids": [Command.set(vat_tax and [vat_tax.id] or [])],
        }
        self._prepare_line_set_account(lvals, product, import_config)
        self._prepare_line_set_global_start_end_dates(lvals, parsed_inv, import_config)
        return lvals

    @api.model
    def parse_invoice(self, invoice_file_bin, invoice_filename, import_config):
        assert invoice_file_bin, "No invoice file"
        assert isinstance(invoice_file_bin, bytes)
        self._update_import_config(import_config)
        import_config.update(
            {
                "filename": invoice_filename,
                "file_bin": invoice_file_bin,
            }
        )
        logger.info(f"Starting to import invoice {invoice_filename}")
        filetype = mimetypes.guess_type(invoice_filename)
        logger.debug("Invoice mimetype: %s", filetype)
        if filetype and filetype[0] in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(invoice_file_bin)
            except Exception as err:
                raise UserError(
                    self.env._(
                        "The XML file '%(filename)s' is not XML-compliant. "
                        "Error: %(err)s",
                        filename=invoice_filename,
                        err=err,
                    )
                ) from None
            pretty_xml_bytes = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_bytes.decode("utf-8"))
            parsed_inv = self.parse_xml_invoice(xml_root, import_config)
            if parsed_inv is False:
                raise UserError(
                    self.env._(
                        "Odoo failed to read the XML invoice '%(filename)s'. "
                        "Did you install the Odoo module to support this type "
                        "of file?",
                        filename=invoice_filename,
                    )
                )
        # Fallback on PDF
        else:
            parsed_inv = self.parse_pdf_invoice(invoice_file_bin, import_config)
        return parsed_inv

    #    @api.model
    #    def _pre_process_parsed_inv(self, parsed_inv, import_config):
    # TODO this method is not called any more, but we may restore it one day
    # Rounding totals
    #        self._pre_process_parsed_inv_rounding(parsed_inv, company)
    #        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
    #            return parsed_inv
    # Support the 2 refund methods; if method a) is used, we convert to
    # method b)
    #        if not parsed_inv.get("type"):
    #            parsed_inv["type"] = "in_invoice"  # default value
    #        if (
    #            parsed_inv["type"] == "in_invoice"
    #            and "amount_total" in parsed_inv
    #            and parsed_inv["currency_rec"].compare_amounts(
    #                parsed_inv["amount_total"], 0
    #            )
    #            < 0
    #        ):
    #            parsed_inv["type"] = "in_refund"
    #            for entry in ["amount_untaxed", "amount_total"]:
    #                parsed_inv[entry] *= -1
    #            for line in parsed_inv.get("lines", []):
    #                line["qty"] *= -1
    #                if "price_subtotal" in line:
    #                    line["price_subtotal"] *= -1
    # Handle taxes:
    # self._pre_process_parsed_inv_taxes(parsed_inv, company)
    # return parsed_inv

    @api.model
    def _pre_process_parsed_inv_taxes(
        self, parsed_inv, company, force_no_vat_deduction=False
    ):
        """Handle taxes in pre_processing parsed invoice."""
        # Handle the case where we import an invoice with VAT in a company that
        # cannot deduct VAT
        if parsed_inv["type"] in ("in_invoice", "in_refund") and (
            company._cannot_refund_vat() or force_no_vat_deduction
        ):
            parsed_inv["amount_tax"] = 0
            parsed_inv["amount_untaxed"] = parsed_inv["amount_total"]
            prec_price = self.env["decimal.precision"].precision_get("Product Price")
            for line in parsed_inv.get("lines", []):
                if line.get("taxes"):
                    if len(line["taxes"]) > 1:
                        parsed_inv["chatter_msg"].append(
                            self.env._(
                                "You are importing an invoice in company %(company)s "
                                "that cannot deduct VAT and the imported invoice has "
                                "several VAT taxes on the same line (%(line)s). We do "
                                "not support this scenario for the moment.",
                                line=line.get("name"),
                                company=company.display_name,
                            )
                        )
                    vat_rate = line["taxes"][0].get("amount")
                    if not float_is_zero(vat_rate, precision_digits=2):
                        price_unit = line["price_unit"] * (1 + vat_rate / 100.0)
                        line["price_unit"] = float_round(
                            price_unit, precision_digits=prec_price
                        )
                        line.pop("price_subtotal")
                        line["taxes"] = []

    @api.model
    def _invoice_already_exists(self, parsed_inv, import_config):
        invoice_number = parsed_inv.get("BT-1")
        if not invoice_number:
            return False
        is_refund = is_credit_note(parsed_inv)
        domain = [
            ("company_id", "=", import_config["company"].id),
        ]
        if import_config["invoice_type"] == "in":
            commercial_partner = import_config.get("partner")
            if not commercial_partner:
                return False
            move_type = is_refund and "in_refund" or "in_invoice"
            domain += [
                ("move_type", "=", move_type),
                ("commercial_partner_id", "=", commercial_partner.id),
                ("ref", "=like", invoice_number),
            ]
            match_log = (
                f"with move type '{move_type}' partner "
                f"'{commercial_partner.display_name}' and reference '{invoice_number}'"
            )
        else:
            move_type = is_refund and "out_refund" or "out_invoice"
            domain += [("name", "=", invoice_number), ("move_type", "=", move_type)]
            match_log = (
                f"with move type '{move_type}' and invoice number '{invoice_number}'"
            )

        existing_inv = self.env["account.move"].search(domain, limit=1)
        if existing_inv:
            msg = (
                f"Found existing invoice {existing_inv.display_name} "
                f"ID {existing_inv.id} {match_log}"
            )
            self._warning_log(import_config, msg)
            import_config["action_warnings"].append(
                self.env._(
                    "Invoice '%(filename)s' already exists in Odoo: %(existing_inv)s.",
                    filename=import_config.get("filename"),
                    existing_inv=existing_inv.display_name,
                )
            )
        else:
            msg = f"No existing invoice found {match_log}"
            self._info_log(import_config, msg)
        return existing_inv

    @api.model
    def _prepare_speedy(self):
        """speedy is a data structure embedded into import_config
        that is used to store the fixed data dictionnaries that are
        designed to speed-up (country_code2id, currency_code2id, ...)
        """
        currency_code2id = {
            cur["name"]: cur["id"]
            for cur in self.env["res.currency"]
            .with_context(active_test=False)
            .search_read([], ["name"])
        }
        all_countries = self.env["res.country"].search_read([], ["code"])
        country_code2id = {cou["code"]: cou["id"] for cou in all_countries}
        country_id2code = {cou["id"]: cou["code"] for cou in all_countries}
        installed_langs = [
            lang["code"] for lang in self.env["res.lang"].search_read([], ["code"])
        ]
        uom_unece2rec = {
            uom.unece_code: uom
            for uom in self.env["uom.uom"].search([("unece_code", "!=", False)])
        }
        untdid_5153_code2label = {
            unece["code"]: unece["name"]
            for unece in self.env["unece.code.list"].search_read(
                [("type", "=", "tax_type")], ["name", "code"]
            )
        }
        incoterms_code2id = {
            inc["code"]: inc["id"]
            for inc in self.env["account.incoterms"]
            .with_context(active_test=False)
            .search_read([], ["code"])
        }
        speedy = {
            "currency_code2id": currency_code2id,
            "country_code2id": country_code2id,
            "country_id2code": country_id2code,
            "incoterms_code2id": incoterms_code2id,
            "installed_langs": installed_langs,
            "uom_unece2rec": uom_unece2rec,
            "untdid_5153_code2label": untdid_5153_code2label,
        }
        return speedy

    # IMPORT CONFIG
    #  REQUIRED FIELDS when calling public method with import_config arg:
    # - company (recordset) or company_id (useful in webservice mode)
    # FIELDS that are always set after _update_import_config() are marked with (A)
    # FIELDS that are always set after _commercial_partner_update_import_config()
    # are marked with (cPA)
    # It is important that fields that have a default value such as "if_already_exists"
    # are always set after _update_import_config() so that the default value is set
    # in a single place in the code
    # {
    ###
    # 'company': company recordset,  # required field
    # 'company_id': company ID  # for useful for webservice mode
    # 'invoice_type': 'in' or 'out'  # (A) defaults to 'in'
    # 'action_warnings': []  # (A) warnings for the notif pop-up for the user
    # when the wizard is used
    # 'global_warnings': [],  # (A) global warnings for the HTML field import_warnings
    # 'line_warnings': [],  # (A) per-line warnings for the HTML field import_warnings
    # 'logs': [],  # (A) invoice import logs
    # 'filename': 'invoice_sample.pdf',
    # 'file_bin': <bytes>  # file as bytes (NOT base64)
    # 'create_bank_account': True or False,
    # 'webservice_mode': True or False,  # if True, create_invoice() returns
    # an invoice ID
    # "if_already_exists": "return_false",  # (A) possible values :
    #                                            raise, match, return_false (default)
    # "start_end_dates_installed": True or False  # (A) True is OCA module
    # account_invoice_start_end_dates is installed
    # "debug_disable_company_check": True or False,
    # 'partner': partner recordset,   # force a partner. When this key is used,
    # it already has with_company(company)
    # 'partner_id': ID  # same as previous field, for webservice
    # 'email_from': "Alexis de Lattre <alexis@akretion.com>",  # for message_new()
    # 'sale_journal': sale journal recordset,  # used to force a journal
    # 'sale_journal_id': ID  # same as previous field, for webservice mode
    # 'purchase_journal': purchase journal recordset,  # used to force a journal
    # 'purchase_journal_id': ID  # same as previous field, for webservice mode
    # 'origin': 'invoice origin',  # set the 'invoice_origin' char field
    # 'invoice_extra_vals': {},  # extra values for invoice create()
    # 'vat_tax2rec': {},  # (A)  sale or purchase tax properties to recordset
    # (sale or purchase tax depend on 'invoice_type')
    # 'updated': True,  # technical key just to avoid double processing
    # of _update_import_config()
    # FIELDS below are set by _commercial_partner_update_import_config()
    # 'shrink_lines': False,  # selection: single/per_vat_rate
    # 'analytic_distribution': Analytic distribution,
    # 'account': Account recordset,
    # 'taxes': taxes multi-recordset,
    # 'label': 'Force invoice line description',
    # 'product': product recordset,
    # 'previous_invoice': invoice recordset,  # used
    # FIELDS below are set by ????
    # 'invoice_currency': currency recordset,  # set by ...
    # 'speedy: {  # (A)
    #     'currency_code2id': {}, 'country_code2id': {}, 'incoterms_code2id': {},
    #     'installed_langs': {}, 'uom_unece2rec': {}, 'untdid_5153_code2label': {},
    #     },
    # }

    @api.model
    def _update_import_config(self, import_config, speedy=None):
        # VERY IMPORTANT: add public methods that accept import_config
        # as argument must call _update_import_config() at the beginning
        # of the method. The "updated" key ensures that we don't do this
        # several times
        assert isinstance(import_config, dict)
        if import_config.get("updated"):
            return
        # to make it work from JSON-RPC
        if not import_config.get("company") and import_config.get("company_id"):
            import_config["company"] = self.env["res.company"].browse(
                import_config["company_id"]
            )
        company = import_config.get("company")
        if not company:
            raise UserError(self.env._("Missing company in the import configuration."))
        if not import_config.get("invoice_type"):
            import_config["invoice_type"] = "in"
        if import_config["invoice_type"] not in ("out", "in"):
            raise UserError(
                self.env._(
                    "Wrong value for 'invoice_type' key in "
                    "import configuration (%s)",
                    import_config["invoice_type"],
                )
            )
        # I set global_warnings like this so that devs can inject a warnings
        # before calling create_invoice() for example
        if not import_config.get("global_warnings"):
            import_config["global_warnings"] = []
        if not import_config.get("if_already_exists"):
            import_config["if_already_exists"] = "return_false"  # set default value
        if import_config["if_already_exists"] not in ("raise", "match", "return_false"):
            raise UserError(
                self.env._(
                    "Wrong value for 'if_already_exists' key in import_config (%s).",
                    import_config["if_already_exists"],
                )
            )
        if not import_config.get("speedy"):
            if speedy is None:
                import_config["speedy"] = self._prepare_speedy()
            else:
                import_config["speedy"] = speedy
        line_model = self.env["account.move.line"]
        start_end_dates_installed = (
            hasattr(line_model, "start_date")
            and hasattr(line_model, "end_date")
            or False
        )
        type_tax_use = import_config["invoice_type"] == "in" and "purchase" or "sale"
        tax_domain = [
            ("type_tax_use", "=", type_tax_use),
            ("company_id", "=", company.id),
            ("unece_type_code", "=", "VAT"),
            ("unece_categ_code", "!=", False),
            ("price_include", "=", False),
            ("amount_type", "=", "percent"),
        ]
        vat_tax2rec = {
            (
                tax.unece_categ_code,
                int(round(tax.amount * 100)),
                tax.tax_exigibility,
            ): tax
            for tax in self.env["account.tax"].search(tax_domain, order="amount desc")
        }

        import_config.update(
            {
                "create_bank_account": company.invoice_import_create_bank_account,
                "action_warnings": [],
                "logs": [],
                # key = import_invoice_line_identifier ; value = list of logs
                "line_warnings": defaultdict(list),
                "start_end_dates_installed": start_end_dates_installed,
                "vat_tax2rec": vat_tax2rec,
            }
        )
        # we may have a partner key in import config when create_invoice() is called
        # from outside of this module
        if import_config.get("partner_id") and not import_config.get("partner"):
            import_config["partner"] = (
                self.env["res.partner"]
                .browse(import_config["partner_id"])
                .with_company(import_config["company"])
            )
        # Same as for 'company': allow journal ID to make it work with JSON+RPC
        if (
            import_config["invoice_type"] == "out"
            and import_config.get("sale_journal_id")
            and not import_config.get("sale_journal")
        ):
            import_config["sale_journal"] = self.env["account.journal"].browse(
                import_config["sale_journal_id"]
            )
        elif (
            import_config["invoice_type"] == "in"
            and import_config.get("purchase_journal_id")
            and not import_config.get("purchase_journal")
        ):
            import_config["purchase_journal"] = self.env["account.journal"].browse(
                import_config["purchase_journal_id"]
            )
        import_config["updated"] = True

    def _invoice_currency_update_import_config(self, parsed_inv, import_config):
        if not import_config.get("invoice_currency"):
            if parsed_inv.get("BT-5"):
                currency_code2id = import_config["speedy"]["currency_code2id"]
                currency_id = currency_code2id.get(parsed_inv["BT-5"])
                if currency_id:
                    currency = self.env["res.currency"].browse(currency_id)
                    if not currency.active:
                        import_config["global_warnings"].append(
                            self.env._(
                                "Currency %s is inactive in Odoo: "
                                "you should activate it.",
                                currency.name,
                            )
                        )
                else:
                    import_config["global_warnings"].append(
                        self.env._(
                            "Currency ISO code '%(invoice_currency_code)s' not found "
                            "in Odoo: using company currency "
                            "'%(company_currency_code)s'.",
                            invoice_currency_code=parsed_inv["BT-5"],
                            company_currency_code=import_config[
                                "company"
                            ].currency_id.name,
                        )
                    )
                    currency = import_config["company"].currency_id
            else:
                currency = import_config["company"].currency_id
            import_config["invoice_currency"] = currency

    def import_invoices_button(self):
        """Method called by the button of the wizard"""
        self.ensure_one()
        if not self.invoice_attachment_ids:
            raise UserError(self.env._("You must select the vendor bills to import."))

        invoice_ids = []
        speedy = self._prepare_speedy()
        action_warnings = []
        for attach in self.invoice_attachment_ids:
            import_config = {
                "company": self.company_id,
                "origin": self.env._("Import of file %s", attach.name),
                "debug_disable_company_check": self.debug_disable_company_check,
            }
            self._update_import_config(import_config, speedy)
            parsed_inv = self.parse_invoice(attach.raw, attach.name, import_config)
            invoice = self.create_invoice(parsed_inv, import_config)
            if invoice:
                invoice_ids.append(invoice.id)
            action_warnings += import_config.get("action_warnings")

        next_action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        if len(invoice_ids) > 1:
            next_action["domain"] = [("id", "in", invoice_ids)]
        elif len(invoice_ids) == 1:
            views = [view for view in next_action["views"] if view[1] == "form"]
            next_action.update(
                {
                    "view_mode": "form,list,kanban",
                    "view_id": False,
                    "views": views,
                    "res_id": invoice_ids[0],
                }
            )
        else:
            if action_warnings:
                raise UserError("\n".join(action_warnings))
            raise UserError(self.env._("No invoice created."))
        msg_type = "success"
        sticky = False
        if action_warnings:
            msg_type = "warning"
            sticky = True
        sticky = bool(action_warnings)
        action_warnings.append(
            self.env._("%s vendor bill(s) created", len(invoice_ids))
        )
        action = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": msg_type,
                "title": self.env._("Import Vendor Bills"),
                "message": "\n".join(action_warnings),
                "next": next_action,
                "sticky": sticky,
            },
        }
        return action

    def _check_import_company(self, parsed_inv, import_config):
        if import_config.get("debug_disable_company_check") or self.env.context.get(
            "edi_skip_company_check"
        ):
            return True
        company_dict = self._get_company_dict(parsed_inv, import_config)
        if not company_dict:
            return True
        raw_vat = company_dict.get("vat_identifier")
        company = import_config["company"]
        if raw_vat:
            invoice_vat = (
                "".join(x for x in raw_vat if not x.isspace()).upper() or False
            )
            import_company_vat = company.partner_id.vat
            if import_company_vat:
                if import_company_vat != invoice_vat:
                    raise UserError(
                        self.env._(
                            "Trying to import invoice in company %(company)s "
                            "that has VAT number '%(import_company_vat)s' "
                            "but the invoice to import contains VAT number "
                            "'%(invoice_vat)s'",
                            company=company.display_name,
                            import_company_vat=import_company_vat,
                            invoice_vat=invoice_vat,
                        )
                    )
                else:
                    msg = (
                        f"Importing invoice in company {company.display_name} that "
                        f"has VAT number {import_company_vat}: it matches the "
                        "VAT number written in the invoice"
                    )
                    self._info_log(import_config, msg)
            else:
                msg = (
                    f"Company {import_config['company'].display_name} has no "
                    "VAT number, so we can't check that we are importing in the "
                    "right company using VAT number"
                )
                self._warning_log(import_config, msg)
        else:
            msg = (
                "No VAT number for our company in the invoice we are importing, "
                "so we can't check that we are importing in the right company "
                "using VAT number"
            )
            self._warning_log(import_config, msg)

    @api.model
    def create_invoice(self, parsed_inv, import_config):
        parsed_inv_for_log = get_data_dict_copy_for_logs(parsed_inv)
        logger.info(f"Start to create invoice from data {parsed_inv_for_log}")
        self._update_import_config(import_config)
        self._invoice_currency_update_import_config(parsed_inv, import_config)
        amo = self.env["account.move"]
        partner = import_config.get("partner")
        # if called from outside of this module, the partner may be already known,
        # (for example when creating a customer invoice or module simple_pdf)
        if not partner:
            partner = self._match_partner(parsed_inv, import_config)
        if partner:
            partner_wc = partner.with_company(import_config["company"])
            import_config["partner"] = partner_wc
            commercial_partner = partner_wc.commercial_partner_id
            import_config["commercial_partner"] = commercial_partner
            commercial_partner._commercial_partner_update_import_config(import_config)
        #  self._pre_process_parsed_inv(parsed_inv, import_config)
        self._check_import_company(parsed_inv, import_config)
        existing_inv = self._invoice_already_exists(parsed_inv, import_config)
        if existing_inv:
            if import_config.get("if_already_exists") == "raise":
                raise UserError(
                    self.env._(
                        "Invoice already exists in Odoo: %(existing_inv)s",
                        existing_inv=existing_inv.display_name,
                    )
                )
            elif import_config.get("if_already_exists") == "match":
                if import_config[
                    "currency"
                ] == existing_inv.currency_id and not import_config[
                    "currency"
                ].compare_amounts(parsed_inv["BT-112"], existing_inv.amount_total):
                    return existing_inv
                else:
                    raise UserError(
                        self.env._(
                            "The invoice to import already exists (%(existing_inv)s) "
                            "but it's total amount (%(existing_inv_total_amount)s) "
                            "doesn't match the total amount of the invoice to import "
                            "(%(import_inv_total_amount)s).",
                            existing_inv=existing_inv.display_name,
                            existing_inv_total_amount=format_amount(
                                self.env,
                                existing_inv.amount_total,
                                existing_inv.currency_id,
                            ),
                            import_inv_total_amount=format_amount(
                                self.env,
                                parsed_inv["BT-112"],
                                import_config["currency"],
                            ),
                        )
                    )

            else:
                return False

        vals = self._prepare_create_invoice_vals(parsed_inv, import_config)
        logger.debug("Invoice vals for creation: %s", vals)
        invoice = amo.create(vals)
        self._post_process_invoice(parsed_inv, import_config, invoice)
        logger.info("Invoice ID %d created", invoice.id)
        chatter_msg = self._prepare_chatter_message(parsed_inv, import_config)
        if chatter_msg:
            invoice.message_post(body=Markup(chatter_msg))
        if import_config.get("webservice_mode"):
            return invoice.id
        return invoice

    def _prepare_chatter_message(self, parsed_inv, import_config):
        chatter_msg = [
            self.env._("This invoice has been created automatically via file import.")
        ]
        if import_config.get("origin"):
            label = self.env._("Origin:")
            chatter_msg.append(f"{label} <strong>{import_config['origin']}</strong>.")
        if import_config.get("logs"):
            label = self.env._("Detailed import logs below:")
            logs = []
            for log_level, msg in import_config["logs"]:
                if log_level == "info":
                    logs.append(
                        f'<span style="color: green; font-weight: bold">'
                        f"INFO </span>{msg}"
                    )
                elif log_level == "warning":
                    logs.append(
                        f'<span style="color: orange; font-weight: bold">'
                        f"WARNING </span>{msg}"
                    )
                elif log_level == "error":
                    logs.append(
                        f'<span style="color: red; font-weight: bold">'
                        f"ERROR </span>{msg}"
                    )
            chatter_msg.append(f"{label}<p>{'<br>'.join(logs)}</p>")
        return " ".join(chatter_msg)

    @api.model
    def _prepare_global_adjustment_line(self, diff_amount, invoice, import_config):
        cur = invoice.currency_id
        diff_amount_cmp = cur.compare_amounts(diff_amount, 0)
        company = invoice.company_id
        # TODO : if a product or account is forced,
        # I think we should use this account (and product) ?
        if diff_amount_cmp > 0:
            if not company.adjustment_debit_account_id:
                raise UserError(
                    self.env._(
                        "You must configure the 'Adjustment Debit Account' "
                        "on the Accounting Configuration page of company %(company)s.",
                        company=company.display_name,
                    )
                )
            account = company.adjustment_debit_account_id
            sign = 1
        else:
            if not company.adjustment_credit_account_id:
                raise UserError(
                    self.env._(
                        "You must configure the 'Adjustment Credit Account' "
                        "on the Accounting Configuration page of company %(company)s.",
                        company=company.display_name,
                    )
                )
            account = company.adjustment_credit_account_id
            sign = -1
        if invoice.fiscal_position_id:
            account = invoice.fiscal_position_id.map_account(account)

        lvals = {
            "move_id": invoice.id,
            "display_type": "product",
            "name": self.env._("Adjustment"),
            "account_id": account.id,
            "quantity": sign,
            "price_unit": diff_amount * sign,
        }
        logger.debug("Prepared global adjustment invoice line %s", lvals)
        return lvals

    def _prepare_adjustment_line(self, iline, diff_amount):
        vals = {
            "move_id": iline.move_id.id,
            "display_type": "product",
            "account_id": iline.account_id.id,
            "name": self.env._("Adjustment on %s") % iline.name,
            "quantity": 1,
            "price_unit": diff_amount,
            "tax_ids": [Command.set(iline.tax_ids.ids)],
        }
        return vals

    @api.model
    def _post_process_invoice(self, parsed_inv, import_config, invoice):
        if import_config.get("invoice_type") == "out":
            return
        amlo = self.env["account.move.line"]
        inv_cur = invoice.currency_id
        # If untaxed amount is wrong, create adjustment lines
        # TODO wrong when DEEE !!!
        if invoice.currency_id.compare_amounts(
            parsed_inv["BT-109"], invoice.amount_untaxed
        ):
            # Try to find the line that has a problem
            for i in range(len(parsed_inv["BG-25"])):
                if "price_subtotal" not in parsed_inv["BG-25"][i]:
                    continue
                # TODO continue... at the moment, it will quit here
                iline = invoice.invoice_line_ids[i]
                odoo_subtotal = iline.price_subtotal
                parsed_subtotal = parsed_inv["lines"][i]["price_subtotal"]
                diff_amount = inv_cur.round(parsed_subtotal - odoo_subtotal)
                if not inv_cur.is_zero(diff_amount):
                    logger.info(
                        "Price subtotal difference found on invoice line %d "
                        "(source:%s, odoo:%s, diff:%s).",
                        i + 1,
                        parsed_subtotal,
                        odoo_subtotal,
                        diff_amount,
                    )
                    # Add the adjustment line
                    vals = self._prepare_adjustment_line(iline, diff_amount)
                    adj_line = amlo.create(vals)
                    logger.info("Adjustment invoice line created ID %d", adj_line.id)
        # Fallback: create global adjustment line
        if invoice.currency_id.compare_amounts(
            parsed_inv["BT-109"], invoice.amount_untaxed
        ):
            diff_amount = inv_cur.round(parsed_inv["BT-109"] - invoice.amount_untaxed)
            parsed_amount_untaxed_fmt = format_amount(
                self.env, parsed_inv["BT-109"], invoice.currency_id
            )
            amount_untaxed_fmt = format_amount(
                self.env, invoice.amount_untaxed, invoice.currency_id
            )
            msg = (
                f"Amount untaxed difference found: source "
                f"{parsed_amount_untaxed_fmt}, odoo {amount_untaxed_fmt}, "
                f"diff {format_amount(self.env, diff_amount, invoice.currency_id)}"
            )
            self._info_log(import_config, msg)
            lvals = self._prepare_global_adjustment_line(
                diff_amount, invoice, import_config
            )
            mline = amlo.create(lvals)
            logger.info("Global adjustment invoice line created ID %d", mline.id)
        assert not invoice.currency_id.compare_amounts(
            parsed_inv["BT-109"], invoice.amount_untaxed
        )
        # Force tax amount if necessary
        if invoice.currency_id.compare_amounts(
            invoice.amount_total, parsed_inv["BT-112"]
        ):
            initial_amount_tax = invoice.amount_tax
            invoice._check_total_amount(parsed_inv["BT-112"])
            # 2 scenarios: forcing tax total was not possible (because
            # there is no tax at all in invoice lines for example) or
            # it worked
            if invoice.currency_id.compare_amounts(
                invoice.amount_total, parsed_inv["BT-112"]
            ):
                import_config["global_warnings"].append(
                    self.env._(
                        "<strong>The total amount of the imported invoice is "
                        "%(real_amount_total)s whereas the total amount computed by "
                        "Odoo is %(current_amount_total)s</strong>. It is the "
                        "consequence of a difference between the total tax amount of "
                        "the invoice (%(real_amount_tax)s) and the total tax amount "
                        "computed by Odoo (%(current_amount_tax)s). "
                        "This is often caused by missing taxes in invoice lines due to "
                        "a failure to find the tax in Odoo that correspond to the tax "
                        "in the imported invoice or missing configuration of taxes "
                        "on products or missing configuration of "
                        "<em>Default Taxes</em> on the partner "
                        "(if there are no products on invoice lines).",
                        real_amount_total=format_amount(
                            self.env, parsed_inv["BT-112"], invoice.currency_id
                        ),
                        current_amount_total=format_amount(
                            self.env, invoice.amount_total, invoice.currency_id
                        ),
                        real_amount_tax=format_amount(
                            self.env,
                            parsed_inv["BT-112"] - parsed_inv["BT-109"],
                            invoice.currency_id,
                        ),
                        current_amount_tax=format_amount(
                            self.env, invoice.amount_tax, invoice.currency_id
                        ),
                    )
                )

            else:
                import_config["global_warnings"].append(
                    self.env._(
                        "The <strong>total tax amount</strong> has been "
                        "<strong>forced</strong> to %(forced_amount)s (amount "
                        "computed by Odoo was: %(initial_amount)s).",
                        forced_amount=format_amount(
                            self.env, invoice.amount_tax, invoice.currency_id
                        ),
                        initial_amount=format_amount(
                            self.env, initial_amount_tax, invoice.currency_id
                        ),
                    )
                )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Process the message data from a fetchmail configuration

        The caller expects us to create a record so we always return an empty
        one even though the actual result is the imported invoice, if the
        message content allows it.
        """
        logger.info(
            "New email received. "
            "Date: %s, Message ID: %s. "
            "Executing "
            "with user ID %d",
            msg_dict.get("date"),
            msg_dict.get("message_id"),
            self.env.user.id,
        )
        # It seems that the "Odoo-way" to handle multi-company in E-mail
        # gateways is by using mail.aliases associated with users that
        # don't switch company (I haven't found any other way), which
        # is not convenient because you may have to create new users
        # for that purpose only. So I implemented my own mechanism,
        # based on the destination email address.
        # This method is called (indirectly) by the fetchmail cron which
        # is run by default as admin and retreive all incoming email in
        # all email accounts. We want to keep this default behavior,
        # and, in multi-company environnement, differentiate the company
        # per destination email address
        company_id = False
        all_companies = self.env["res.company"].search_read(
            [], ["invoice_import_email"]
        )
        if len(all_companies) > 1:  # multi-company setup
            for company in all_companies:
                if company["invoice_import_email"]:
                    company_dest_email = company["invoice_import_email"].strip()
                    if company_dest_email in msg_dict.get(
                        "to", ""
                    ) or company_dest_email in msg_dict.get("cc", ""):
                        company_id = company["id"]
                        logger.info(
                            "Matched message %s: importing invoices in company ID %d",
                            msg_dict["message_id"],
                            company_id,
                        )
                        break
            if not company_id:
                logger.error(
                    "Mail gateway in multi-company setup: mail ignored. "
                    "No destination found for message_id = %s.",
                    msg_dict["message_id"],
                )
                return self.create({})
        else:  # mono-company setup
            company_id = all_companies[0]["id"]

        self = self.with_company(company_id)
        if msg_dict.get("attachments"):
            i = 0
            for attach in msg_dict["attachments"]:
                i += 1
                filename = attach.fname
                filetype = mimetypes.guess_type(filename)
                if filetype[0] not in (
                    "application/xml",
                    "text/xml",
                    "application/pdf",
                ):
                    logger.info(
                        "Attachment %d: %s skipped because not an XML nor PDF.",
                        i,
                        filename,
                    )
                    continue
                logger.info(
                    "Attachment %d: %s. Trying to import it as an invoice",
                    i,
                    filename,
                )
                # if it's an XML file, attach.content is a string
                # if it's a PDF file, attach.content is a byte !
                if isinstance(attach.content, str):
                    attach_bytes = attach.content.encode("utf-8")
                else:
                    attach_bytes = attach.content
                origin = self.env._(
                    "email sent by <strong>%(email_from)s</strong> on %(date)s "
                    "with subject <strong>%(subject)s</strong>",
                    email_from=msg_dict.get("email_from")
                    and html.escape(msg_dict["email_from"]),
                    date=msg_dict.get("date"),
                    subject=msg_dict.get("subject")
                    and html.escape(msg_dict["subject"]),
                )
                company = self.env
                import_config = {
                    "company_id": company_id,
                    "email_from": msg_dict.get("email_from"),
                    "origin": origin,
                    # "debug_disable_company_check": True,
                }

                try:
                    parsed_inv = self.parse_invoice(
                        attach_bytes, filename, import_config
                    )
                    invoice = self.create_invoice(parsed_inv, import_config)
                    logger.info(
                        f"Invoice ID {invoice.id} created from "
                        f"email attachment {filename}."
                    )
                except Exception as err:
                    logger.error(
                        f"Failed to import invoice from mail attachment {filename}. "
                        f"Error: {err}"
                    )
        else:
            logger.info("The email has no attachments, skipped.")
        return self.create({})

    def _get_partner_dict(self, parsed_inv, import_config):
        if import_config["invoice_type"] == "in":
            partner_dict = parsed_inv.get("BG-4")
        else:
            partner_dict = parsed_inv.get("BG-7")
        return partner_dict or {}

    def _get_company_dict(self, parsed_inv, import_config):
        if import_config["invoice_type"] == "in":
            company_dict = parsed_inv.get("BG-7")
        else:
            company_dict = parsed_inv.get("BG-4")
        return company_dict or {}

    @api.model
    def _match_partner(self, parsed_inv, import_config):
        partner_dict = self._get_partner_dict(parsed_inv, import_config)
        partner = False
        if partner_dict.get("vat_identifier"):
            raw_vat = partner_dict["vat_identifier"]
            vat = "".join(x for x in raw_vat if not x.isspace()).upper() or False
            if vat:
                partner = self.env["res.partner"].search(
                    [
                        ("vat", "=", vat),
                        # ('parent_id', '=', False),
                        ("company_id", "in", (import_config["company"].id, False)),
                    ],
                    limit=1,
                )
                if partner:
                    msg = f"Partner '{partner.display_name}' matched via VAT number"
                    self._info_log(import_config, msg)
                    return partner
        if import_config.get("email_from"):
            _partner_name, email = parseaddr(import_config["email_from"])
            if email:
                partner = self.env["res.partner"].search(
                    [
                        ("email", "=like", email),
                        ("company_id", "in", (import_config["company"].id, False)),
                    ],
                    limit=1,
                )
                if partner:
                    msg = f"Partner '{partner.display_name}' matched via email"
                    self._info_log(import_config, msg)
                    return partner
        return partner

    @api.model
    def _match_product(self, line_dict, parsed_inv, import_config):
        # parsed_inv is useful when inheriting this method
        # modify the behavior for a specific supplier
        product_obj = self.env["product.product"]
        base_domain = [("company_id", "in", (False, import_config["company"].id))]
        msg_prefix = f"Invoice line {line_dict['BT-126']}:"
        if line_dict.get("BT-157"):
            product = product_obj.search(
                base_domain + [("barcode", "=", line_dict["BT-157"])], limit=1
            )
            if product:
                msg = (
                    f"{msg_prefix} product {product.display_name} "
                    "matched via barcode (BT-157)"
                )
                self._info_log(import_config, msg)
                return product
            else:
                msg = (
                    f"{msg_prefix} no product with barcode '{line_dict['BT-157']}' "
                    "found in Odoo"
                )
                self._info_log(import_config, msg)
        if line_dict.get("BT-156"):
            product = product_obj.search(
                base_domain + [("default_code", "=", line_dict["BT-156"])], limit=1
            )
            if product:
                msg = (
                    f"{msg_prefix} product {product.display_name} matched via buyer "
                    "product identifier (BT-156)"
                )
                self._info_log(import_config, msg)
                return product
            else:
                msg = (
                    f"{msg_prefix} no product with internal reference "
                    f"'{line_dict['BT-156']}' (buyer product identifier BT-156) "
                    "found in Odoo"
                )
                self._info_log(import_config, msg)
        if line_dict.get("BT-155") and import_config.get("commercial_partner"):
            sinfo = self.env["product.supplierinfo"].search(
                base_domain
                + [
                    ("product_code", "=", line_dict["BT-155"]),
                    ("partner_id", "=", import_config["commercial_partner"].id),
                ],
                limit=1,
            )
            if sinfo:
                msg = (
                    f"{msg_prefix} product {product.display_name} matched "
                    "via seller product identifier (BT-155)"
                )
                if sinfo.product_id:
                    self._info_log(import_config, msg)
                    return sinfo.product_id
                if (
                    sinfo.product_tmpl_id
                    and len(sinfo.product_tmpl_id.product_variant_ids) == 1
                ):
                    self._info_log(import_config, msg)
                    return sinfo.product_tmpl_id.product_variant_ids
            else:
                msg = (
                    f"{msg_prefix} no product with code '{line_dict['BT-155']}' "
                    "(seller product identifier BT-155) found in the supplier info "
                    "records of Odoo"
                )
                self._info_log(import_config, msg)
        # msg = f"NO product with code {line_dict['BT-155']}"
        # import_config['line_warnings'][line_dict.get('BT-126')].append(msg)
        return None

    @api.model
    def _match_uom(self, line_dict, parsed_inv, import_config):
        uom_unece2rec = import_config["speedy"]["uom_unece2rec"]
        import_remap = {
            "EA": "C62",
        }
        if line_dict.get("BT-130"):
            if line_dict["BT-130"] in uom_unece2rec:
                return uom_unece2rec[line_dict["BT-130"]]
            if line_dict["BT-130"] in import_remap:
                uom_code = import_remap[line_dict["BT-130"]]
                if uom_code in uom_unece2rec:
                    return uom_unece2rec[uom_code]
            msg = (
                f"Line {line_dict.get('BT-126')}: no unit of measure with "
                f"UNECE code '{line_dict['BT-130']}' in Odoo"
            )
            # import_config['line_warnings'][line_dict.get('BT-126')].append(msg)
            self._warning_log(import_config, msg)
        return False

    def _match_vat_tax_common(
        self, line_ident, vat_categ_code, vat_rate_int, parsed_inv, import_config
    ):
        bt8_to_odoo = {
            "invoice": "on_invoice",
            "delivery": "on_invoice",
            "payment": "on_payment",
        }
        tax_exigibility = (
            parsed_inv.get("BT-8") and bt8_to_odoo.get(parsed_inv["BT-8"]) or False
        )
        msg_prefix = f"Invoice line {line_ident}:"
        vat_tax2rec = import_config["vat_tax2rec"]
        tax = vat_tax2rec.get((vat_categ_code, vat_rate_int, tax_exigibility))
        if tax:
            return tax
        for (tax_vat_categ_code, tax_vat_rate_int, _exig), tax in vat_tax2rec.items():
            if (
                tax_vat_categ_code == vat_categ_code
                and tax_vat_rate_int == vat_rate_int
            ):
                return tax
        for (tax_vat_categ_code, _rate, _exig), tax in vat_tax2rec.items():
            if tax_vat_categ_code == vat_categ_code:
                msg = (
                    f"{msg_prefix} approx match on tax {tax.display_name} "
                    "using only VAT categ code"
                )
                self._warning_log(import_config, msg)
                return tax
        return False

    @api.model
    def _match_vat_tax_bg25(self, line_dict, parsed_inv, import_config):
        vat_categ_code = line_dict.get("BT-151")
        vat_rate_int = (
            line_dict.get("BT-152") and int(round(line_dict["BT-152"] * 100)) or False
        )
        line_ident = line_dict["BT-126"]
        return self._match_vat_tax_common(
            line_ident, vat_categ_code, vat_rate_int, parsed_inv, import_config
        )

    @api.model
    def _match_vat_tax_bg23(self, line_nr, vat_line_dict, parsed_inv, import_config):
        vat_categ_code = vat_line_dict.get("BT-118")
        vat_rate_int = (
            vat_line_dict.get("BT-119")
            and int(round(vat_line_dict["BT-119"] * 100))
            or False
        )
        return self._match_vat_tax_common(
            line_nr, vat_categ_code, vat_rate_int, parsed_inv, import_config
        )

    @api.model
    def _match_bank_account(self, commercial_partner, parsed_inv, import_config):
        assert import_config["invoice_type"] == "in"
        bank_account_number = parsed_inv.get("BT-84")
        bank_acc_obj = self.env["res.partner.bank"]
        if bank_account_number:
            sanitized_acc_number = sanitize_account_number(bank_account_number)
            bank_account = bank_acc_obj.with_context(active_test=False).search(
                [
                    ("partner_id", "=", commercial_partner.id),
                    ("sanitized_acc_number", "=", sanitized_acc_number),
                ],
                limit=1,
            )
            if bank_account:
                msg = (
                    f"Matched on bank account {bank_account.display_name} "
                    "of partner {commercial_partner.display_name} "
                    "(allow_out_payment={bank_account.allow_out_payment})"
                )
                if not bank_account.allow_out_payment:
                    import_config["global_warnings"].append(
                        self.env._(
                            "Matched with bank account "
                            "<strong>%(bank_account)s</strong>, "
                            "but this bank account is not allowed yet "
                            "for outgoing payments.",
                            bank_account=bank_account.display_name,
                        )
                    )
                if not bank_account.active:
                    import_config["global_warnings"].append(
                        self.env._(
                            "Matched with bank account "
                            "<strong>%(bank_account)s</strong>, "
                            "but this bank account is <strong>archived</strong>. "
                            "You should re-activate it.",
                            bank_account=bank_account.display_name,
                        )
                    )
                self._info_log(import_config, msg)
                return bank_account
            if import_config["create_bank_account"]:
                bank_id = False
                bic = parsed_inv.get("BT-86")
                if bic and len(bic) in (8, 11):
                    if len(bic) == 8:
                        alt_bic = f"{bic}XXX"
                        bank_domain = [("bic", "in", (bic, alt_bic))]
                    elif len(bic) == 11 and bic.endswith("XXX"):
                        alt_bic = bic[:8]
                        bank_domain = [("bic", "in", (bic, alt_bic))]
                    else:
                        bank_domain = [("bic", "=", bic)]
                    bank_ids = list(self.env["res.bank"]._search(bank_domain, limit=1))
                    bank_id = bank_ids and bank_ids[0] or False
                country_id2code = import_config["speedy"]["country_id2code"]
                # for SEPA countries, we don't create bank accounts that are not
                # IBANs and where the bank account number doesn't start with the
                # country code
                sepa_country_group = self.env.ref("base.sepa_zone")
                sepa_country_codes = [
                    country_id2code[country.id]
                    for country in sepa_country_group.country_ids
                    if country_id2code.get(country.id)
                ]
                vendor_country_code = parsed_inv.get("BG-4", {}).get("country_code")
                if vendor_country_code and vendor_country_code in sepa_country_codes:
                    if not iban_is_valid(sanitized_acc_number):
                        import_config["global_warnings"].append(
                            self.env._(
                                "Bank account '%(acc_number)s' hasn't been created "
                                "automatically because the vendor's country is in the "
                                "SEPA zone and the bank account number is <strong>not "
                                "a valid IBAN</strong>.",
                                acc_number=sanitized_acc_number,
                            )
                        )
                        return False
                    if not sanitized_acc_number.startswith(vendor_country_code):
                        import_config["global_warnings"].append(
                            self.env._(
                                "Bank account '%(acc_number)s' hasn't been created "
                                "automatically because the vendor's country "
                                "(%(vendor_country_code)s) is different from the "
                                "country of the IBAN.",
                                acc_number=sanitized_acc_number,
                                vendor_country_code=vendor_country_code,
                            )
                        )
                        return False
                vals = {
                    "partner_id": commercial_partner.id,
                    "acc_number": sanitized_acc_number,
                    "bank_id": bank_id,
                }
                if hasattr(bank_acc_obj, "acc_type_manual"):
                    # if OCA module partner_bank_acc_type_constraint is installed
                    if iban_is_valid(sanitized_acc_number):
                        vals["acc_type_manual"] = "iban"
                    else:
                        vals["acc_type_manual"] = "bank"
                bank_account = bank_acc_obj.create(vals)
                import_config["global_warnings"].append(
                    self.env._(
                        "New bank account <strong>%(bank_account)s</strong> created. "
                        "You must check that this bank account really belongs to "
                        "the vendor and then allow it for outgoing payments.",
                        bank_account=bank_account.display_name,
                    )
                )
            else:
                import_config["global_warnings"].append(
                    self.env._(
                        "The electronic invoice states the bank account number "
                        "<strong>%(bank_account_number)s</strong>, "
                        "but this bank account doesn't exist in Odoo for partner "
                        "<em>%(commercial_partner)s</em> and the option to "
                        "auto-create bank accounts upon invoice import is not enabled.",
                        bank_account_number=bank_account_number,
                        commercial_partner=commercial_partner.display_name,
                    )
                )
                return bank_account
        return False

    @api.model
    def _info_log(self, import_config, msg):
        logger.info(msg)
        import_config["logs"].append(("info", msg))

    @api.model
    def _warning_log(self, import_config, msg):
        logger.warning(msg)
        import_config["logs"].append(("warning", msg))

    @api.model
    def _error_log(self, import_config, msg):
        logger.error(msg)
        import_config["logs"].append(("error", msg))

    @api.model
    def _get_lang_from_country_code(self, country_code, import_config):
        assert country_code
        try:
            locale = Locale.parse(f"und_{country_code.upper()}")
            country_lang_code = locale.language
        except Exception as err:
            msg = f"Failed to get lang from country code '{country_code}': Error: {err}"
            self._warning_log(import_config, msg)
            return False
        full_lang_code = f"{country_lang_code}_{country_code}"
        installed_langs = import_config["speedy"]["installed_langs"]
        for lang_code in installed_langs:
            if lang_code == full_lang_code:
                return lang_code
        for lang_code in installed_langs:
            if country_lang_code == lang_code[:2]:
                return lang_code
        return False
