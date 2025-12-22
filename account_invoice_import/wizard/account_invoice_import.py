# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# Copyright 2020-2021 Therp BV (https://therp.nl)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import html
import logging
import mimetypes
from datetime import datetime
from email.utils import parseaddr

from lxml import etree

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_is_zero, float_round
from odoo.tools.misc import format_amount

logger = logging.getLogger(__name__)


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

    @api.model
    def parse_xml_invoice(self, xml_root, company):
        return False

    @api.model
    def parse_pdf_invoice(self, file_data, company):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_statement_import_*
        modules"""
        xml_files_dict = self.env["pdf.helper"].pdf_get_xml_files(file_data)
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            parsed_inv = self.parse_xml_invoice(xml_root, company)
            if parsed_inv:
                return parsed_inv
        parsed_inv = self.fallback_parse_pdf_invoice(file_data, company)
        if not parsed_inv:
            parsed_inv = {}
        return parsed_inv

    def fallback_parse_pdf_invoice(self, file_data, company):
        """Designed to be inherited by the module
        account_invoice_import_invoice2data, to be sure the invoice2data
        technique is used after the electronic invoice modules such as
        account_invoice_import_facturx and account_invoice_import_ubl
        """
        return False

        # INVOICE PIVOT format ('parsed_inv' without pre-processing)
        # For refunds, we support 2 possibilities:
        # a) type = 'in_invoice' with negative amounts and qty
        # b) type = 'in_refund' with positive amounts and qty ("Odoo way")
        # That way, it simplifies the code in the format-specific import
        # modules, which is what we want!
        # {
        # 'type': 'in_invoice' or 'in_refund'  # 'in_invoice' by default
        # 'journal': {'code': 'PUR'},  # use only if you want to force
        #                              # a specific journal
        # 'currency': {
        #    'iso': 'EUR',
        #    'country_code': 'FR',
        #    'currency_symbol': '€',  # The one or the other
        #    },
        # 'date': '2015-10-08',  # Must be a string
        # 'date_due': '2015-11-07',
        # 'date_start': '2015-10-01',  # for services over a period of time
        # 'date_end': '2015-10-31',
        # 'amount_untaxed': 10.0,
        # 'amount_tax': 2.0,  # provide amount_untaxed OR amount_tax
        # 'amount_total': 12.0,  # Total with taxes, must always be provided
        # 'partner': {
        #       'vat': 'FR25499247138',
        #       'email': 'support@browserstack.com',
        #       'name': 'Capitaine Train',
        #       'street': '27 rue Henri Rolland',
        #       'street2': 'ZAC des cactus',
        #       'city': 'Villeurbanne',
        #       'zip': '69100',
        #       'country_code': 'FR',
        #       'state_code': False,
        #       'phone': '+33 4 72 42 24 42',
        #       'mobile': '+33 6 42 12 42 12',
        #       },
        # 'company': {'vat': 'FR12123456789'}, # Rarely set in invoices
        #                                      # Only used to check we are not
        #                                      # importing the invoice in the
        #                                      # wrong company by mistake
        # 'invoice_number': 'I1501243',
        # 'description': 'TGV Paris-Lyon',
        # 'attachments': {'file1.pdf': base64data1, 'file2.pdf': base64data2},
        # 'chatter_msg': ['Notes added in chatter of the invoice'],
        # 'note': 'Note embedded in the document',
        # 'origin': 'Origin note',
        # 'lines': [{
        #       # Regular product line:
        #       'product': {
        #           'barcode': '4123456000021',
        #           'code': 'GZ250',
        #           },
        #       'name': 'Gelierzucker Extra 250g',
        #       'price_unit': 1.45, # price_unit without taxes
        #       'discount': 10.0,  # for 10% discount
        #       'qty': 2.0,
        #       'price_subtotal': 2.61,  # not required, but needed
        #               to be able to generate adjustment lines when decimal
        #               precision is not high enough in Odoo
        #       'uom': {'unece_code': 'C62'},
        #       'taxes': [{
        #           'amount_type': 'percent',
        #           'amount': 20.0,
        #           'unece_type_code': 'VAT',
        #           'unece_categ_code': 'S',
        #           'unece_due_date_code': '432',
        #           }],
        #       'date_start': '2015-10-01',
        #       'date_end': '2015-10-31',
        #       # date_start and date_end on lines override the global value
        #       },
        #       # Section header line (display_type='line_section'):
        #       {
        #           'sectionheader': 'Section Title',  # Creates a section header line
        #       },
        #       # Note line (display_type='line_note'):
        #       {
        #           'line_note': 'Note text here',  # Creates a note line
        #       }],
        # }
        # IMPORT CONFIG
        # {
        # 'company': company recordset,  # required field
        # 'single_line': False,  # boolean
        # 'analytic_distribution': Analytic distribution,
        # 'account': Account recordset,
        # 'taxes': taxes multi-recordset,
        # 'label': 'Force invoice line description',
        # 'product': product recordset,
        # 'previous_invoice': invoice recordset,  # used
        # }
        #
        # Note: we also support importing customer invoices via
        # create_invoice() but only with single_line = False

    @api.model
    def _prepare_create_invoice_no_partner(self, parsed_inv, import_config, vals):
        if parsed_inv.get("partner"):
            if parsed_inv["partner"].get("email"):
                source_email = parsed_inv["partner"]["email"]
                if parsed_inv["partner"].get("name"):
                    source_email = "%s <%s>" % (
                        parsed_inv["partner"]["name"],
                        source_email,
                    )
                vals["invoice_source_email"] = source_email
            partner_data = {
                "is_company": True,
                "country_id": False,
                "state_id": False,
                "supplier_rank": 1,
            }
            if (
                parsed_inv["partner"].get("country_code")
                and isinstance(parsed_inv["partner"]["country_code"], str)
                and len(parsed_inv["partner"]["country_code"].strip()) == 2
            ):
                country = self.env["res.country"].search(
                    [
                        (
                            "code",
                            "=",
                            parsed_inv["partner"]["country_code"].upper().strip(),
                        )
                    ],
                    limit=1,
                )
                if country:
                    partner_data["country_id"] = country.id
                # There are already warnings when country code doesn't exist
            if (
                partner_data.get("country_id")
                and parsed_inv["partner"].get("state_code")
                and isinstance(parsed_inv["partner"]["state_code"], str)
            ):
                state = self.env["res.country.state"].search(
                    [
                        (
                            "code",
                            "=",
                            parsed_inv["partner"]["state_code"].upper().strip(),
                        ),
                        ("country_id", "=", partner_data["country_id"]),
                    ],
                    limit=1,
                )
                if state:
                    partner_data["state_id"] = state.id
            rpo = self.env["res.partner"]
            for key, value in parsed_inv["partner"].items():
                if (
                    value
                    and isinstance(value, str)
                    and hasattr(rpo, key)
                    and key not in ("country_code", "state_code")
                ):
                    partner_data[key] = value
            vals["import_partner_data"] = partner_data

    @api.model
    def _prepare_create_invoice_journal(self, parsed_inv, import_config, vals):
        if parsed_inv["type"] in ("in_invoice", "in_refund") and import_config.get(
            "journal"
        ):
            vals["journal_id"] = import_config["journal"].id
        elif parsed_inv.get("journal"):
            journal = self.env["business.document.import"]._match_journal(
                parsed_inv["journal"],
                parsed_inv["chatter_msg"],
                company=import_config["company"],
                raise_exception=False,
            )
            if (
                parsed_inv["type"] in ("in_invoice", "in_refund")
                and journal.type != "purchase"
            ):
                raise UserError(
                    _(
                        "You are importing a vendor bill/refund in journal '%s' "
                        "which is not a purchase journal."
                    )
                    % journal.display_name
                )
            elif (
                parsed_inv["type"] in ("out_invoice", "out_refund")
                and journal.type != "sale"
            ):
                raise UserError(
                    _(
                        "You are importing a customer invoice/refund in journal '%s' "
                        "which is not a sale journal."
                    )
                    % journal.display_name
                )
            vals["journal_id"] = journal.id
        else:
            # we don't rely on auto-set of journal, because we need the journal
            # to get the default account
            if parsed_inv["type"] in ("out_invoice", "out_refund"):
                journal_type = "sale"
            else:
                journal_type = "purchase"
            journal = self.env["account.journal"].search(
                [
                    ("company_id", "=", import_config["company"].id),
                    ("type", "=", journal_type),
                ],
                limit=1,
            )
            if not journal:
                raise UserError(
                    _(
                        "No journal with type %(journal_type)s in company %(company)s.",
                        company=import_config["company"].display_name,
                        journal_type=journal._fields["type"].convert_to_export(
                            journal_type, journal
                        ),
                    )
                )
            vals["journal_id"] = journal.id

    @api.model
    def _prepare_create_invoice_vals(self, parsed_inv, import_config):
        assert parsed_inv.get("pre-processed"), "pre-processing not done"
        company = import_config["company"]
        bdio = self.env["business.document.import"]
        vals = {
            "move_type": parsed_inv["type"],
            "company_id": company.id,
            "invoice_origin": parsed_inv.get("origin"),
            "ref": parsed_inv.get("invoice_number"),
            "narration": parsed_inv.get("narration", ""),
            "invoice_date": parsed_inv.get("date"),
            "invoice_line_ids": [],
        }
        if parsed_inv["type"] in ("out_invoice", "out_refund"):
            partner_type = "customer"
        else:
            partner_type = "supplier"
        partner = None
        if parsed_inv.get("partner"):
            partner = bdio.with_company(company.id)._match_partner(
                parsed_inv["partner"],
                parsed_inv["chatter_msg"],
                partner_type=partner_type,
                raise_exception=False,
            )
        if partner:
            partner = partner.commercial_partner_id.with_company(company.id)
            vals["partner_id"] = partner.id
            self._set_previous_invoice(parsed_inv, import_config, partner)
            self._update_import_config_from_previous_invoice(import_config)
        else:
            self._prepare_create_invoice_no_partner(parsed_inv, import_config, vals)
        if parsed_inv.get("currency"):
            currency = bdio._match_currency(
                parsed_inv["currency"],
                parsed_inv["chatter_msg"],
                company=import_config["company"],
                raise_exception=False,
            )
            vals["currency_id"] = currency.id
        self._prepare_create_invoice_journal(parsed_inv, import_config, vals)
        # Force due date of the invoice
        if parsed_inv.get("date_due"):
            vals["invoice_date_due"] = parsed_inv["date_due"]
            # Set invoice_payment_term_id to False because the due date is
            # set by invoice_date + invoice_payment_term_id otherwise
            vals["invoice_payment_term_id"] = False
        # Bank info
        if parsed_inv.get("iban") and vals["move_type"] == "in_invoice" and partner:
            partner_bank = bdio.with_company(company.id)._match_partner_bank(
                partner,
                parsed_inv["iban"],
                parsed_inv.get("bic"),
                parsed_inv["chatter_msg"],
                create_if_not_found=company.invoice_import_create_bank_account,
            )
            if partner_bank:
                vals["partner_bank_id"] = partner_bank.id
        self._last_update_import_config(parsed_inv, import_config, vals)
        # invoice lines
        if parsed_inv.get("lines") and not import_config.get("single_line"):
            self._prepare_line_vals_nline(parsed_inv, import_config, vals, partner)
        else:
            self._prepare_line_vals_1line(parsed_inv, import_config, vals, partner)
        # if module account_invoice_check_total from OCA/account-invoicing is installed
        if hasattr(self.env["account.move"], "check_total"):
            vals["check_total"] = parsed_inv["amount_total"]
        return vals

    @api.model
    def _prepare_line_vals_1line(self, parsed_inv, import_config, vals, partner):
        il_vals = {
            "display_type": "product",
            "quantity": 1,
        }
        if import_config.get("label"):
            il_vals["name"] = import_config["label"]
        elif parsed_inv.get("description"):
            il_vals["name"] = parsed_inv["description"]
        # For the moment, we only take into account the 'price_include'
        # option of the first tax
        taxes = self.env["account.tax"]
        if import_config.get("product"):
            product = import_config["product"]
            il_vals["product_id"] = product.id
            if parsed_inv["type"] in ("out_invoice", "out_refund"):
                account = product._get_product_accounts()["income"]
                product_taxes = product.taxes_id
            else:
                account = product._get_product_accounts()["expense"]
                product_taxes = product.supplier_taxes_id
            taxes = product_taxes.filtered(
                lambda tax: tax.company_id == import_config["company"]
            )
        else:
            if import_config.get("account"):
                account = import_config["account"]
            if import_config.get("taxes"):
                taxes = import_config["taxes"]
        fp = partner and partner.property_account_position_id or False
        if fp:
            account = fp.map_account(account)
            taxes = fp.map_tax(taxes)
        il_vals.update(
            {
                "account_id": account.id,
                "tax_ids": [Command.set(taxes.ids)],
            }
        )
        if taxes and taxes[0].price_include:
            il_vals["price_unit"] = parsed_inv.get("amount_total")
        else:
            il_vals["price_unit"] = parsed_inv.get("amount_untaxed")
        if (
            import_config["start_end_dates_installed"]
            and parsed_inv.get("date_start")
            and parsed_inv.get("date_end")
        ):
            il_vals["start_date"] = parsed_inv.get("date_start")
            il_vals["end_date"] = parsed_inv.get("date_end")

        vals["invoice_line_ids"].append(Command.create(il_vals))

    @api.model
    def _prepare_line_vals_nline(self, parsed_inv, import_config, vals, partner):
        assert parsed_inv.get("lines")
        bdio = self.env["business.document.import"]
        for line in parsed_inv["lines"]:
            # Handle special display types first
            if line.get("line_note"):
                il_vals = {
                    "product_id": None,
                    "name": line.get("line_note"),
                    "display_type": "line_note",
                }
                vals["invoice_line_ids"].append(Command.create(il_vals))
                continue
            if line.get("sectionheader"):
                il_vals = {
                    "product_id": None,
                    "name": line.get("sectionheader"),
                    "display_type": "line_section",
                }
                vals["invoice_line_ids"].append(Command.create(il_vals))
                continue
            product = False
            if line.get("product"):
                product = bdio._match_product(
                    line["product"],
                    parsed_inv["chatter_msg"],
                    seller=partner,
                    raise_exception=False,
                )
            if not product and import_config.get("product"):
                product = import_config["product"]
            if product:
                product = product.with_company(import_config["company"].id)
                if parsed_inv["type"] in ("out_invoice", "out_refund"):
                    account = product._get_product_accounts()["income"]
                    product_taxes = product.taxes_id
                else:
                    account = product._get_product_accounts()["expense"]
                    product_taxes = product.supplier_taxes_id
                taxes = product_taxes.filtered(
                    lambda tax: tax.company_id == import_config["company"]
                )
            else:
                account = import_config["account"]
                taxes = import_config["taxes"]
            if not taxes:
                if parsed_inv["type"] in ("out_invoice", "out_refund"):
                    type_tax_use = "sale"
                else:
                    type_tax_use = "purchase"
                taxes = bdio._match_taxes(
                    line.get("taxes"),
                    parsed_inv["chatter_msg"],
                    company=import_config["company"],
                    type_tax_use=type_tax_use,
                    raise_exception=False,
                )

            fp = partner and partner.property_account_position_id or False
            if fp:
                account = fp.map_account(account)
                taxes = fp.map_tax(taxes)
            uom = bdio._match_uom(
                line.get("uom"),
                parsed_inv["chatter_msg"],
                product=product,
                raise_exception=False,
            )

            il_vals = {
                "display_type": "product",
                "product_id": product and product.id or False,
                "product_uom_id": uom.id,
                "account_id": account.id,
                "tax_ids": [Command.set(taxes.ids)],
                "quantity": line["qty"],
                "price_unit": line["price_unit"],  # TODO add support for tax incl ?
                "discount": line.get("discount", 0),
            }

            if import_config.get("label"):
                il_vals["name"] = import_config["label"]
            elif line.get("name"):
                il_vals["name"] = line["name"]
            if import_config["start_end_dates_installed"]:
                il_vals["start_date"] = line.get("date_start") or parsed_inv.get(
                    "date_start"
                )
                il_vals["end_date"] = line.get("date_end") or parsed_inv.get("date_end")
            vals["invoice_line_ids"].append(Command.create(il_vals))

    @api.model
    def _set_previous_invoice(self, parsed_inv, import_config, partner):
        if not import_config.get("previous_invoice"):
            domain = [
                ("company_id", "=", import_config["company"].id),
                ("commercial_partner_id", "=", partner.id),
                ("state", "=", "posted"),
            ]
            if parsed_inv["type"] in ("out_invoice", "out_refund"):
                domain.append(("move_type", "in", ("out_invoice", "out_refund")))
            else:
                domain.append(("move_type", "in", ("in_invoice", "in_refund")))
            inv = self.env["account.move"].search(domain, limit=1, order="date desc")
            if inv:
                import_config["previous_invoice"] = inv

    @api.model
    def _update_import_config_from_previous_invoice(self, import_config):
        if import_config.get("previous_invoice"):
            inv = import_config["previous_invoice"]
            ilines = inv.invoice_line_ids.filtered(
                lambda x: x.display_type == "product"
            )
            if ilines:
                iline = ilines[0]
                if not import_config.get("product") and iline.product_id:
                    import_config["product"] = iline.product_id
                else:
                    if not import_config.get("account") and iline.account_id:
                        import_config["account"] = iline.account_id
                    if not import_config.get("taxes") and iline.tax_ids:
                        import_config["taxes"] = iline.tax_ids

    def _last_update_import_config(self, parsed_inv, import_config, vals):
        # if import_config settings are empty, get from global params
        # import_config['product']: inject with_company()
        # import_config['taxes']: filter on company and type_tax_use
        # import_config['account']: check the company
        # set import_config['start_end_dates_installed']
        if not import_config.get("taxes"):
            if parsed_inv["type"] in ("out_invoice", "out_refund"):
                import_config["taxes"] = import_config["company"].account_sale_tax_id
            else:
                import_config["taxes"] = import_config[
                    "company"
                ].account_purchase_tax_id
        if not import_config.get("account"):
            journal = self.env["account.journal"].browse(vals["journal_id"])
            import_config["account"] = journal.default_account_id
        if not import_config.get("account"):
            import_config["account"] = (
                self.env["ir.property"]
                .with_company(import_config["company"].id)
                ._get("property_account_expense_categ_id", "account.account")
            )
        if import_config.get("product"):
            import_config["product"] = import_config["product"].with_company(
                import_config["company"].id
            )
        # Cleanup data
        if import_config["taxes"]:
            if parsed_inv["type"] in ("out_invoice", "out_refund"):
                type_tax_use = "sale"
            else:
                type_tax_use = "purchase"
            import_config["taxes"] = import_config["taxes"].filtered(
                lambda x: x.company_id.id == import_config["company"].id
                and x.type_tax_use == type_tax_use
            )
        if (
            import_config["account"]
            and import_config["account"].company_id.id != import_config["company"].id
        ):
            import_config["account"] = False
        # set 'start_end_dates_installed' if the OCA module account_invoice_start_end_dates
        # from https://github.com/OCA/account-closing is installed
        line_model = self.env["account.move.line"]
        import_config["start_end_dates_installed"] = (
            hasattr(line_model, "start_date")
            and hasattr(line_model, "end_date")
            or False
        )

    @api.model
    def parse_invoice(
        self, invoice_file_b64, invoice_filename, company, email_from=None
    ):
        assert invoice_file_b64, "No invoice file"
        assert isinstance(invoice_file_b64, bytes)
        logger.info("Starting to import invoice %s", invoice_filename)
        file_data = base64.b64decode(invoice_file_b64)
        filetype = mimetypes.guess_type(invoice_filename)
        logger.debug("Invoice mimetype: %s", filetype)
        if filetype and filetype[0] in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(file_data)
            except Exception as e:
                raise UserError(
                    _("This XML file is not XML-compliant. Error: %s") % e
                ) from None
            pretty_xml_bytes = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_bytes.decode("utf-8"))
            parsed_inv = self.parse_xml_invoice(xml_root, company)
            if parsed_inv is False:
                raise UserError(
                    _(
                        "This type of XML invoice is not supported. "
                        "Did you install the module to support this type "
                        "of file?"
                    )
                )
        # Fallback on PDF
        else:
            parsed_inv = self.parse_pdf_invoice(file_data, company)
        if "attachments" not in parsed_inv:
            parsed_inv["attachments"] = {}
        parsed_inv["attachments"][invoice_filename] = invoice_file_b64
        if email_from:
            if "partner" not in parsed_inv:
                parsed_inv["partner"] = {}
            partner_name, email = parseaddr(email_from)
            if not parsed_inv["partner"].get("email"):
                parsed_inv["partner"]["email"] = email
            if partner_name and not parsed_inv["partner"].get("name"):
                parsed_inv["partner"]["name"] = partner_name
        pp_parsed_inv = self._pre_process_parsed_inv(parsed_inv, company)
        return pp_parsed_inv

    @api.model
    def _pre_process_parsed_inv(self, parsed_inv, company):
        if parsed_inv.get("pre-processed"):
            return parsed_inv
        parsed_inv["pre-processed"] = True
        if "chatter_msg" not in parsed_inv:
            parsed_inv["chatter_msg"] = []
        if not parsed_inv.get("currency_rec"):
            parsed_inv["currency_rec"] = self.env[
                "business.document.import"
            ]._match_currency(
                parsed_inv.get("currency"), [], company=company, raise_exception=False
            )
        # Rounding totals
        self._pre_process_parsed_inv_rounding(parsed_inv, company)
        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
            return parsed_inv
        if "amount_total" not in parsed_inv:
            # Designed to allow the import of an empty invoice with
            # 1 invoice line at 0 that has the right account/product/analytic
            parsed_inv["amount_total"] = 0
        if "amount_tax" in parsed_inv and "amount_untaxed" not in parsed_inv:
            parsed_inv["amount_untaxed"] = (
                parsed_inv["amount_total"] - parsed_inv["amount_tax"]
            )
        elif "amount_untaxed" not in parsed_inv and "amount_tax" not in parsed_inv:
            # For invoices that never have taxes
            parsed_inv["amount_untaxed"] = parsed_inv["amount_total"]
        # Support the 2 refund methods; if method a) is used, we convert to
        # method b)
        if not parsed_inv.get("type"):
            parsed_inv["type"] = "in_invoice"  # default value
        if (
            parsed_inv["type"] == "in_invoice"
            and "amount_total" in parsed_inv
            and parsed_inv["currency_rec"].compare_amounts(
                parsed_inv["amount_total"], 0
            )
            < 0
        ):
            parsed_inv["type"] = "in_refund"
            for entry in ["amount_untaxed", "amount_total"]:
                parsed_inv[entry] *= -1
            for line in parsed_inv.get("lines", []):
                line["qty"] *= -1
                if "price_subtotal" in line:
                    line["price_subtotal"] *= -1
        # Handle taxes:
        self._pre_process_parsed_inv_taxes(parsed_inv, company)
        parsed_inv_for_log = dict(parsed_inv)
        if "attachments" in parsed_inv_for_log:
            parsed_inv_for_log.pop("attachments")
        logger.debug("Result of invoice parsing parsed_inv=%s", parsed_inv_for_log)
        # the 'company' dict in parsed_inv is NOT used to auto-detect
        # the company, but to check that we are not importing an
        # invoice for another company by mistake
        if (
            parsed_inv.get("company")
            and not config["test_enable"]
            and not self.env.context.get("edi_skip_company_check")
        ):
            self.env["business.document.import"]._check_company(
                parsed_inv["company"],
                parsed_inv["chatter_msg"],
                company,
                raise_exception=True,
            )
        return parsed_inv

    @api.model
    def _pre_process_parsed_inv_rounding(self, parsed_inv, company):
        for entry in ["amount_untaxed", "amount_total", "amount_tax"]:
            if entry in parsed_inv:
                parsed_inv[entry] = parsed_inv["currency_rec"].round(parsed_inv[entry])
        prec_price = self.env["decimal.precision"].precision_get("Product Price")
        prec_disc = self.env["decimal.precision"].precision_get("Discount")
        prec_qty = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in parsed_inv.get("lines", []):
            if line.get("sectionheader") or line.get("line_note"):
                continue
            line["qty"] = float_round(line.get("qty", 0), precision_digits=prec_qty)
            line["price_unit"] = float_round(
                line.get("price_unit", 0), precision_digits=prec_price
            )
            line["discount"] = float_round(
                line.get("discount", 0), precision_digits=prec_disc
            )

    @api.model
    def _pre_process_parsed_inv_taxes(self, parsed_inv, company):
        """Handle taxes in pre_processing parsed invoice."""
        # Handle the case where we import an invoice with VAT in a company that
        # cannot deduct VAT
        if (
            parsed_inv["type"] in ("in_invoice", "in_refund")
            and company._cannot_refund_vat()
        ):
            parsed_inv["amount_tax"] = 0
            parsed_inv["amount_untaxed"] = parsed_inv["amount_total"]
            prec_price = self.env["decimal.precision"].precision_get("Product Price")
            for line in parsed_inv.get("lines", []):
                if line.get("taxes"):
                    if len(line["taxes"]) > 1:
                        parsed_inv["chatter_msg"].append(
                            _(
                                "You are importing an invoice in company %(company)s that "
                                "cannot deduct VAT and the imported invoice has "
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
    def _invoice_already_exists(self, parsed_inv, commercial_partner, company_id):
        if not parsed_inv.get("invoice_number"):
            return False
        existing_inv = self.env["account.move"].search(
            [
                ("company_id", "=", company_id),
                ("commercial_partner_id", "=", commercial_partner.id),
                ("move_type", "=", parsed_inv["type"]),
                ("ref", "=ilike", parsed_inv["invoice_number"]),
            ],
            limit=1,
        )
        return existing_inv

    def import_invoices(self):
        """Method called by the button of the wizard"""
        self.ensure_one()
        company = self.company_id
        if not self.invoice_attachment_ids:
            raise UserError(_("You must select the vendor bills to import."))

        invoice_ids = []
        warnings = []
        for attach in self.invoice_attachment_ids:
            parsed_inv = self.parse_invoice(attach.datas, attach.name, company)
            import_config = {"company": company}
            if parsed_inv.get("partner"):
                partner = (
                    self.env["business.document.import"]
                    .with_company(self.company_id.id)
                    ._match_partner(
                        parsed_inv["partner"],
                        parsed_inv["chatter_msg"],
                        raise_exception=False,
                    )
                )
                if partner:
                    # To speed-up next match
                    parsed_inv["partner"] = {"recordset": partner}
                    existing_inv = self._invoice_already_exists(
                        parsed_inv, partner.commercial_partner_id, company.id
                    )
                    if existing_inv:
                        logger.warning(
                            "This invoice already exists "
                            "in Odoo (ID %d number %s supplier number %s)",
                            existing_inv.id,
                            existing_inv.name,
                            parsed_inv.get("invoice_number"),
                        )
                        warnings.append(
                            _(
                                "Invoice '%(filename)s' already exists in Odoo: "
                                "%(existing_inv)s.",
                                filename=attach.name,
                                existing_inv=existing_inv.display_name,
                            )
                        )
                        continue

                    import_config = partner._convert_to_import_config(company)
            invoice = self.create_invoice(
                parsed_inv,
                import_config,
                origin=_("Import of file %s", attach.name),
            )
            invoice_ids.append(invoice.id)

        next_action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        if len(invoice_ids) > 1:
            next_action["domain"] = [("id", "in", invoice_ids)]
        elif len(invoice_ids) == 1:
            views = [view for view in next_action["views"] if view[1] == "form"]
            next_action.update(
                {
                    "view_mode": "form,tree,kanban",
                    "view_id": False,
                    "views": views,
                    "res_id": invoice_ids[0],
                }
            )
        else:
            if warnings:
                raise UserError("\n".join(warnings))
            raise UserError(_("No invoice created."))
        action = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Import Vendor Bills"),
                "message": _("%d vendor bill(s) created", len(invoice_ids)),
                "next": next_action,
            },
        }
        if warnings:
            action["params"].update(
                {
                    "type": "warning",
                    "message": "\n".join(warnings),
                    "sticky": True,
                }
            )
        return action

    @api.model
    def create_invoice(self, parsed_inv, import_config, origin=None):
        amo = self.env["account.move"]
        parsed_inv = self._pre_process_parsed_inv(parsed_inv, import_config["company"])
        vals = self._prepare_create_invoice_vals(parsed_inv, import_config)
        logger.debug("Invoice vals for creation: %s", vals)
        invoice = amo.create(vals)
        self._post_process_invoice(parsed_inv, import_config, invoice)
        logger.info("Invoice ID %d created", invoice.id)
        self.env["business.document.import"].post_create_or_update(parsed_inv, invoice)
        invoice.message_post(
            body=_(
                "This invoice has been created automatically via file import. "
                "Origin: <strong>%s</strong>."
            )
            % (origin or _("unspecified"))
        )
        return invoice

    # TODO v18: move company_id to regular arg before origin
    @api.model
    def create_invoice_webservice(
        self,
        invoice_file_b64,
        invoice_filename,
        origin,
        company_id=None,
        email_from=None,
    ):
        # for invoice_file_b64, we accept it as bytes AND str
        # to avoid "Object of type bytes is not JSON serializable"
        assert invoice_file_b64
        if isinstance(invoice_file_b64, str):
            invoice_file_b64 = invoice_file_b64.encode("utf8")
        assert isinstance(invoice_file_b64, bytes)
        assert isinstance(invoice_filename, str)
        if company_id is None:
            company = self.env.company
            company_id = company.id
        else:
            company = self.env["res.company"].browse(company_id)
        logger.info(
            "Starting to import invoice file %s in company ID %d",
            invoice_filename,
            company_id,
        )
        parsed_inv = self.parse_invoice(
            invoice_file_b64, invoice_filename, company, email_from=email_from
        )
        partner = (
            self.env["business.document.import"]
            .with_company(company_id)
            ._match_partner(
                parsed_inv["partner"], parsed_inv["chatter_msg"], raise_exception=False
            )
        )
        if partner:
            partner = partner.commercial_partner_id
            # To avoid a second full _match_partner() inside create_invoice()
            parsed_inv["partner"]["recordset"] = partner
            existing_inv = self._invoice_already_exists(parsed_inv, partner, company_id)
            if existing_inv:
                logger.warning(
                    "This supplier invoice already exists "
                    "in Odoo (ID %d number %s supplier number %s)",
                    existing_inv.id,
                    existing_inv.name,
                    parsed_inv.get("invoice_number"),
                )
                return False
            import_config = partner._convert_to_import_config(company)
        else:
            import_config = {"company": company}
        invoice = self.create_invoice(parsed_inv, import_config, origin)
        return invoice.id

    @api.model
    def _prepare_global_adjustment_line(self, diff_amount, invoice, import_config):
        cur = invoice.currency_id
        diff_amount_cmp = cur.compare_amounts(diff_amount, 0)
        company = invoice.company_id
        if diff_amount_cmp > 0:
            if not company.adjustment_debit_account_id:
                raise UserError(
                    _(
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
                    _(
                        "You must configure the 'Adjustment Credit Account' "
                        "on the Accounting Configuration page of company %(company)s.",
                        company=company.display_name,
                    )
                )
            account = company.adjustment_credit_account_id
            sign = -1
        if invoice.fiscal_position_id:
            account = invoice.fiscal_position_id.map_account(account)

        il_vals = {
            "move_id": invoice.id,
            "display_type": "product",
            "name": _("Adjustment"),
            "account_id": account.id,
            "quantity": sign,
            "price_unit": diff_amount * sign,
        }
        logger.debug("Prepared global adjustment invoice line %s", il_vals)
        return il_vals

    def _prepare_adjustment_line(self, iline, diff_amount):
        vals = {
            "move_id": iline.move_id.id,
            "display_type": "product",
            "account_id": iline.account_id.id,
            "name": _("Adjustment on %s") % iline.name,
            "quantity": 1,
            "price_unit": diff_amount,
            "tax_ids": [Command.set(iline.tax_ids.ids)],
        }
        return vals

    @api.model
    def _post_process_invoice(self, parsed_inv, import_config, invoice):
        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
            return
        amlo = self.env["account.move.line"]
        inv_cur = invoice.currency_id
        # If untaxed amount is wrong, create adjustment lines
        if parsed_inv["currency_rec"].compare_amounts(
            parsed_inv["amount_untaxed"], invoice.amount_untaxed
        ):
            # Try to find the line that has a problem
            for i in range(len(parsed_inv["lines"])):
                if "price_subtotal" not in parsed_inv["lines"][i]:
                    continue
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
        if parsed_inv["currency_rec"].compare_amounts(
            parsed_inv["amount_untaxed"], invoice.amount_untaxed
        ):
            diff_amount = inv_cur.round(
                parsed_inv["amount_untaxed"] - invoice.amount_untaxed
            )
            logger.info(
                "Amount untaxed difference found " "(source: %s, odoo:%s, diff:%s)",
                parsed_inv["amount_untaxed"],
                invoice.amount_untaxed,
                diff_amount,
            )
            il_vals = self._prepare_global_adjustment_line(
                diff_amount, invoice, import_config
            )
            mline = amlo.create(il_vals)
            logger.info("Global adjustment invoice line created ID %d", mline.id)
        assert not parsed_inv["currency_rec"].compare_amounts(
            parsed_inv["amount_untaxed"], invoice.amount_untaxed
        )
        # Force tax amount if necessary
        if parsed_inv["currency_rec"].compare_amounts(
            invoice.amount_total, parsed_inv["amount_total"]
        ):
            initial_amount_tax = invoice.amount_tax
            invoice._check_total_amount(parsed_inv["amount_total"])
            # 2 scenarios: forcing tax total was not possible (because
            # there is no tax at all in invoice lines for example) or
            # it worked
            if parsed_inv["currency_rec"].compare_amounts(
                invoice.amount_total, parsed_inv["amount_total"]
            ):
                parsed_inv["chatter_msg"].append(
                    _(
                        "<strong>The total amount of the imported invoice is "
                        "%(real_amount_total)s whereas the total amount computed by "
                        "Odoo is %(current_amount_total)s</strong>. It is the consequence "
                        "of a difference between the total tax amount of the invoice "
                        "(%(real_amount_tax)s) and the total tax amount computed by Odoo "
                        "(%(current_amount_tax)s). "
                        "This is often caused by missing taxes in invoice lines due to "
                        "a failure to find the tax in Odoo that correspond to the tax in "
                        "the imported invoice or missing configuration of taxes on products "
                        "or missing configuration of <em>Default Taxes</em> on the partner "
                        "(if there are no products on invoice lines).",
                        real_amount_total=format_amount(
                            self.env, parsed_inv["amount_total"], invoice.currency_id
                        ),
                        current_amount_total=format_amount(
                            self.env, invoice.amount_total, invoice.currency_id
                        ),
                        real_amount_tax=format_amount(
                            self.env,
                            parsed_inv["amount_total"] - parsed_inv["amount_untaxed"],
                            invoice.currency_id,
                        ),
                        current_amount_tax=format_amount(
                            self.env, invoice.amount_tax, invoice.currency_id
                        ),
                    )
                )

            else:
                parsed_inv["chatter_msg"].append(
                    _(
                        "The <strong>total tax amount</strong> has been "
                        "<strong>forced</strong> to %(forced_amount)s (amount computed by "
                        "Odoo was: %(initial_amount)s).",
                        forced_amount=format_amount(
                            self.env, invoice.amount_tax, invoice.currency_id
                        ),
                        initial_amount=format_amount(
                            self.env, initial_amount_tax, invoice.currency_id
                        ),
                    )
                )

    def xpath_to_dict_helper(self, xml_root, xpath_dict, namespaces):
        for key, value in xpath_dict.items():
            if isinstance(value, list):
                isdate = isfloat = ischar_to_clean = False
                if "date" in key:
                    isdate = True
                elif "amount" in key:
                    isfloat = True
                elif key == "name":
                    ischar_to_clean = True
                xpath_dict[key] = self.multi_xpath_helper(
                    xml_root,
                    value,
                    namespaces,
                    isdate=isdate,
                    isfloat=isfloat,
                    ischar_to_clean=ischar_to_clean,
                )
                if not xpath_dict[key]:
                    logger.debug("No value extracted for %s", key)
            elif isinstance(value, dict):
                xpath_dict[key] = self.xpath_to_dict_helper(xml_root, value, namespaces)
        return xpath_dict

    def multi_xpath_helper(
        self,
        xml_root,
        xpath_list,
        namespaces,
        isdate=False,
        isfloat=False,
        ischar_to_clean=False,
    ):
        assert isinstance(xpath_list, list)
        for xpath in xpath_list:
            xpath_res = xml_root.xpath(xpath, namespaces=namespaces)
            if xpath_res and xpath_res[0].text:
                if isdate:
                    if (
                        xpath_res[0].attrib
                        and xpath_res[0].attrib.get("format") != "102"
                    ):
                        raise UserError(_("Only the date format 102 is supported."))
                    date_dt = datetime.strptime(xpath_res[0].text, "%Y%m%d")
                    date_str = fields.Date.to_string(date_dt)
                    return date_str
                elif isfloat:
                    res_float = float(xpath_res[0].text)
                    return res_float
                elif ischar_to_clean:
                    res_char = xpath_res[0].text
                    if res_char and isinstance(res_char, str):
                        # With the experience, we'll probably have more things to clean
                        res_char = res_char.replace("\n", " ")
                    return res_char
                else:
                    return xpath_res[0].text
        return False

    def raw_multi_xpath_helper(self, xml_root, xpath_list, namespaces):
        for xpath in xpath_list:
            xpath_res = xml_root.xpath(xpath, namespaces=namespaces)
            if xpath_res:
                return xpath_res
        return []

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
                origin = _(
                    "email sent by <b>{email_from}</b> on {date} with subject <b>{subject}</b>",
                    email_from=msg_dict.get("email_from")
                    and html.escape(msg_dict["email_from"]),
                    date=msg_dict.get("date"),
                    subject=msg_dict.get("subject")
                    and html.escape(msg_dict["subject"]),
                )
                try:
                    invoice_id = self.create_invoice_webservice(
                        base64.b64encode(attach_bytes),
                        filename,
                        origin,
                        company_id=company_id,
                        email_from=msg_dict.get("email_from"),
                    )
                    logger.info(
                        "Invoice ID %d created from email attachment %s.",
                        invoice_id,
                        filename,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to import invoice from mail attachment %s. Error: %s",
                        filename,
                        e,
                    )
        else:
            logger.info("The email has no attachments, skipped.")
        return self.create({})
