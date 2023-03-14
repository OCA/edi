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

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_compare, float_is_zero, float_round
from odoo.tools.misc import format_amount

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _name = "account.invoice.import"
    _inherit = ["business.document.import", "mail.thread"]
    _description = "Wizard to import supplier invoices/refunds"

    invoice_file = fields.Binary(string="PDF or XML Invoice")
    invoice_filename = fields.Char(string="Filename")
    state = fields.Selection(
        [
            ("import", "Import"),
            ("config", "Select Invoice Import Configuration"),
            ("update", "Update"),
            ("update-from-invoice", "Update From Invoice"),
            ("partner-not-found", "Partner not found"),
        ],
        default="import",
    )
    partner_id = fields.Many2one("res.partner", string="Vendor", readonly=True)
    # The following partner_* fields are used for partner-not-found state
    partner_vat = fields.Char(readonly=True)
    partner_country_id = fields.Many2one("res.country", readonly=True)
    import_config_id = fields.Many2one(
        "account.invoice.import.config", string="Invoice Import Configuration"
    )
    currency_id = fields.Many2one("res.currency", readonly=True)
    invoice_type = fields.Selection(
        [("in_invoice", "Invoice"), ("in_refund", "Refund")],
        string="Invoice or Refund",
        readonly=True,
    )
    amount_untaxed = fields.Float(
        string="Total Untaxed", digits="Account", readonly=True
    )
    amount_total = fields.Float(string="Total", digits="Account", readonly=True)
    invoice_id = fields.Many2one(
        "account.move", string="Draft Supplier Invoice to Update"
    )
    message = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # I can't put 'default_state' in context because then it is transfered
        # to the code and it causes problems when we create invoice lines
        if self.env.context.get("wizard_default_state"):
            res["state"] = self.env.context["wizard_default_state"]
        if self.env.context.get("default_partner_id") and not self.env.context.get(
            "default_import_config_id"
        ):
            configs = self.env["account.invoice.import.config"].search(
                [
                    ("partner_id", "=", self.env.context["default_partner_id"]),
                    ("company_id", "=", self.env.company.id),
                ]
            )
            if len(configs) == 1:
                res["import_config_id"] = configs.id
        return res

    @api.model
    def parse_xml_invoice(self, xml_root):
        return False

    @api.model
    def parse_pdf_invoice(self, file_data):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_statement_import_*
        modules"""
        xml_files_dict = self.get_xml_files_from_pdf(file_data)
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            parsed_inv = self.parse_xml_invoice(xml_root)
            if parsed_inv:
                return parsed_inv
        parsed_inv = self.fallback_parse_pdf_invoice(file_data)
        if not parsed_inv:
            parsed_inv = {}
        return parsed_inv

    def fallback_parse_pdf_invoice(self, file_data):
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
        # "type": "in_invoice" or "in_refund"  # "in_invoice" by default
        # "journal": {"code": "PUR"},  # use only if you want to force
        #                              # a specific journal
        # "currency": {
        #    "iso": "EUR",
        #    "iso_or_symbol": "€",  # The one or the other
        #    "symbol": "$",
        #    "country_code": "US",
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
        #       'street3': '3rd floor',
        #       'city': 'Villeurbanne',
        #       'zip': '69100',
        #       'country_code': 'FR',
        #       'state_code': False,
        #       'phone': '+33 4 72 42 24 42',
        #       'mobile': '+33 4 72 42 24 43',
        #       'ref': 'C1242',
        #       'siren': '123456789',
        #       'coc_registration_number': '123456789',
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
        #       'product': {
        #           'barcode': '4123456000021',
        #           'code': 'GZ250',
        #           },
        #       'name': 'Gelierzucker Extra 250g',
        #       'price_unit': 1.45, # price_unit without taxes
        #       'qty': 2.0,
        #       'price_subtotal': 2.90,  # not required, but needed
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
        #       }],
        # }

        # IMPORT CONFIG
        # {
        # 'invoice_line_method': '1line_no_product',
        # 'account_analytic': Analytic account recordset,
        # 'account': Account recordset,
        # 'taxes': taxes multi-recordset,
        # 'label': 'Force invoice line description',
        # 'product': product recordset,
        # }
        #
        # Note: we also support importing customer invoices via
        # create_invoice() but only with 'nline_*' invoice import methods.

    @api.model
    def _prepare_create_invoice_no_partner(self, parsed_inv, import_config, vals):
        if parsed_inv.get("partner") and parsed_inv["partner"].get("email"):
            source_email = parsed_inv["partner"]["email"]
            if parsed_inv["partner"].get("name"):
                source_email = "%s <%s>" % (
                    parsed_inv["partner"]["name"],
                    source_email,
                )
            vals["invoice_source_email"] = source_email

    @api.model
    def _prepare_create_invoice_journal(self, parsed_inv, import_config, company, vals):
        if parsed_inv["type"] in ("in_invoice", "in_refund") and import_config.get(
            "journal"
        ):
            journal_id = import_config["journal"].id
        elif parsed_inv.get("journal"):
            journal = self.with_company(company.id)._match_journal(
                parsed_inv["journal"], parsed_inv["chatter_msg"]
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
            journal_id = journal.id
        else:
            journal_id = (
                self.env["account.move"]
                .with_context(
                    default_move_type=parsed_inv["type"], company_id=company.id
                )
                ._get_default_journal()
                .id
            )
        vals["journal_id"] = journal_id

    @api.model
    def _prepare_create_invoice_vals(self, parsed_inv, import_config):
        assert parsed_inv.get("pre-processed"), "pre-processing not done"
        amo = self.env["account.move"]
        company = (
            self.env["res.company"].browse(self.env.context.get("force_company"))
            or self.env.company
        )
        vals = {
            "move_type": parsed_inv["type"],
            "company_id": company.id,
            "invoice_origin": parsed_inv.get("origin"),
            "ref": parsed_inv.get("invoice_number"),
            "invoice_date": parsed_inv.get("date"),
            "narration": parsed_inv.get("narration"),
            "payment_reference": parsed_inv.get("payment_reference"),
            "invoice_line_ids": [],
        }
        if parsed_inv["type"] in ("out_invoice", "out_refund"):
            partner_type = "customer"
        else:
            partner_type = "supplier"
        partner = None
        if parsed_inv.get("partner"):
            partner = self._match_partner(
                parsed_inv["partner"],
                parsed_inv["chatter_msg"],
                partner_type=partner_type,
                raise_exception=False,
            )
        if not partner:
            self._prepare_create_invoice_no_partner(parsed_inv, import_config, vals)
            return vals
        partner = partner.commercial_partner_id
        vals["partner_id"] = partner.id
        if parsed_inv.get("currency"):
            currency = self._match_currency(
                parsed_inv.get("currency"), parsed_inv["chatter_msg"]
            )
            vals["currency_id"] = currency.id
        self._prepare_create_invoice_journal(parsed_inv, import_config, company, vals)
        vals["invoice_line_ids"] = []
        vals = amo.play_onchanges(vals, ["partner_id"])
        # Force due date of the invoice
        if parsed_inv.get("date_due"):
            vals["invoice_date_due"] = parsed_inv["date_due"]
            # Set invoice_payment_term_id to False because the due date is
            # set by invoice_date + invoice_payment_term_id otherwise
            vals["invoice_payment_term_id"] = False
        # Bank info
        if parsed_inv.get("iban") and vals["move_type"] == "in_invoice":
            partner_bank = self._match_partner_bank(
                partner,
                parsed_inv["iban"],
                parsed_inv.get("bic"),
                parsed_inv["chatter_msg"],
                create_if_not_found=company.invoice_import_create_bank_account,
            )
            if partner_bank:
                vals["partner_bank_id"] = partner_bank.id
        # get invoice line vals
        vals["invoice_line_ids"] = []
        if import_config.get("invoice_line_method"):
            if import_config["invoice_line_method"].startswith("1line"):
                self._prepare_line_vals_1line(partner, vals, parsed_inv, import_config)
            elif import_config["invoice_line_method"].startswith("nline"):
                if parsed_inv.get("lines"):
                    self._prepare_line_vals_nline(
                        partner, vals, parsed_inv, import_config
                    )
                else:
                    parsed_inv["chatter_msg"].append(
                        _(
                            "You have selected a Multi Line method for this import "
                            "but Odoo could not extract/read information about the "
                            "lines of the invoice. You should update the Invoice Import "
                            "Configuration of "
                            "<a href=# data-oe-model=res.partner data-oe-id=%d>%s</a> "
                            "to set a Single Line method."
                        )
                        % (partner.id, partner.display_name)
                    )

        # Write analytic account + fix syntax for taxes
        analytic_account = import_config.get("account_analytic", False)
        if analytic_account:
            for line in vals["invoice_line_ids"]:
                line[2]["analytic_account_id"] = analytic_account.id
        return vals

    @api.model
    def _prepare_line_vals_1line(self, partner, vals, parsed_inv, import_config):
        line_model = self.env["account.move.line"]
        if import_config["invoice_line_method"] == "1line_no_product":
            if import_config["taxes"]:
                il_tax_ids = [(6, 0, import_config["taxes"].ids)]
            else:
                il_tax_ids = False
            il_vals = {
                "account_id": import_config["account"].id,
                "tax_ids": il_tax_ids,
                "price_unit": parsed_inv.get("amount_untaxed"),
            }
        elif import_config["invoice_line_method"] == "1line_static_product":
            product = import_config["product"]
            il_vals = {"product_id": product.id, "move_id": vals}
            il_vals = line_model.play_onchanges(il_vals, ["product_id"])
            il_vals.pop("move_id")
        if import_config.get("label"):
            il_vals["name"] = import_config["label"]
        elif parsed_inv.get("description"):
            il_vals["name"] = parsed_inv["description"]
        self.set_1line_price_unit_and_quantity(il_vals, parsed_inv)
        self.set_1line_start_end_dates(il_vals, parsed_inv)
        vals["invoice_line_ids"].append((0, 0, il_vals))

    @api.model
    def _prepare_line_vals_nline(self, partner, vals, parsed_inv, import_config):
        assert parsed_inv.get("lines")
        line_model = self.env["account.move.line"]
        start_end_dates_installed = hasattr(line_model, "start_date") and hasattr(
            line_model, "end_date"
        )
        static_vals = {"move_id": None}
        if import_config["invoice_line_method"] == "nline_no_product":
            static_vals = {"account_id": import_config["account"].id, "move_id": None}
        elif import_config["invoice_line_method"] == "nline_static_product":
            sproduct = import_config["product"]
            static_vals = {"product_id": sproduct.id, "move_id": vals}
            static_vals = line_model.play_onchanges(static_vals, ["product_id"])
        for line in parsed_inv["lines"]:
            il_vals = static_vals.copy()
            if import_config["invoice_line_method"] == "nline_auto_product":
                if not line.get("line_note") and not line.get("sectionheader"):
                    product = self._match_product(
                        line["product"], parsed_inv["chatter_msg"], seller=partner
                    )
                    il_vals = {"product_id": product.id, "move_id": vals}
                    il_vals = line_model.play_onchanges(il_vals, ["product_id"])
            elif import_config["invoice_line_method"] == "nline_no_product":
                taxes = self._match_taxes(line.get("taxes"), parsed_inv["chatter_msg"])
                il_vals["tax_ids"] = [(6, 0, taxes.ids)]
            if not il_vals.get("account_id") and il_vals.get("product_id"):
                product = self.env["product.product"].browse(il_vals["product_id"])
                raise UserError(
                    _(
                        "Account missing on product '%s' or on it's related "
                        "category '%s'."
                    )
                    % (product.display_name, product.categ_id.display_name)
                )
            if line.get("name"):
                il_vals["name"] = line["name"]
            if line.get("line_note"):
                il_vals = {
                    "product_id": None,
                    "move_id": vals,
                    "name": line.get("line_note"),
                    "display_type": "line_note",
                }
            if line.get("sectionheader"):
                il_vals = {
                    "product_id": None,
                    "move_id": vals,
                    "name": line.get("sectionheader"),
                    "display_type": "line_section",
                }
            if "display_type" not in il_vals:  # it is not a line note or sectionheader
                uom = self._match_uom(line.get("uom"), parsed_inv["chatter_msg"])
                il_vals["product_uom_id"] = uom.id
                il_vals.update(
                    {
                        "quantity": line["qty"],
                        "price_unit": line["price_unit"],  # TODO fix for tax incl
                    }
                )
            if start_end_dates_installed:
                il_vals["start_date"] = line.get("date_start") or parsed_inv.get(
                    "date_start"
                )
                il_vals["end_date"] = line.get("date_end") or parsed_inv.get("date_end")
            il_vals = line_model.play_onchanges(il_vals, ["product_id"])
            il_vals.pop("move_id", None)
            vals["invoice_line_ids"].append((0, 0, il_vals))

    @api.model
    def set_1line_price_unit_and_quantity(self, il_vals, parsed_inv):
        """For the moment, we only take into account the 'price_include'
        option of the first tax"""
        il_vals["quantity"] = 1
        il_vals["price_unit"] = parsed_inv.get("amount_total")
        if il_vals.get("tax_ids"):
            for tax_entry in il_vals["tax_ids"]:
                if tax_entry:
                    tax_id = False
                    if tax_entry[0] == 4:
                        tax_id = tax_entry[1]
                    elif tax_entry[0] == 6:
                        tax_id = tax_entry[2][0]
                    if tax_id:
                        first_tax = self.env["account.tax"].browse(tax_id)
                        if not first_tax.price_include:
                            il_vals["price_unit"] = parsed_inv.get("amount_untaxed")
                            break

    @api.model
    def set_1line_start_end_dates(self, il_vals, parsed_inv):
        """Only useful if you have installed the module account_cutoff_prepaid
        from https://github.com/OCA/account-closing"""
        amlo = self.env["account.move.line"]
        if (
            parsed_inv.get("date_start")
            and parsed_inv.get("date_end")
            and hasattr(amlo, "start_date")
            and hasattr(amlo, "end_date")
        ):
            il_vals["start_date"] = parsed_inv.get("date_start")
            il_vals["end_date"] = parsed_inv.get("date_end")

    def company_cannot_refund_vat(self):
        company_id = self.env.context.get("force_company") or self.env.company.id
        vat_purchase_taxes = self.env["account.tax"].search(
            [
                ("company_id", "=", company_id),
                ("amount_type", "=", "percent"),
                ("type_tax_use", "=", "purchase"),
            ]
        )
        if not vat_purchase_taxes:
            return True
        return False

    @api.model
    def parse_invoice(self, invoice_file_b64, invoice_filename, email_from=None):
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
                raise UserError(_("This XML file is not XML-compliant. Error: %s") % e)
            pretty_xml_bytes = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_bytes.decode("utf-8"))
            parsed_inv = self.parse_xml_invoice(xml_root)
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
            parsed_inv = self.parse_pdf_invoice(file_data)
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
        # pre_process_parsed_inv() will be called again a second time,
        # but it's OK
        pp_parsed_inv = self.pre_process_parsed_inv(parsed_inv)
        return pp_parsed_inv

    @api.model
    def pre_process_parsed_inv(self, parsed_inv):
        if parsed_inv.get("pre-processed"):
            return parsed_inv
        parsed_inv["pre-processed"] = True
        if "chatter_msg" not in parsed_inv:
            parsed_inv["chatter_msg"] = []
        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
            return parsed_inv
        if not parsed_inv.get("currency_rounding"):
            self.get_precision_rounding_from_currency_helper(parsed_inv)
        prec_pp = self.env["decimal.precision"].precision_get("Product Price")
        prec_uom = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
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
            and float_compare(
                parsed_inv["amount_total"],
                0,
                precision_rounding=parsed_inv["currency_rounding"],
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
        self._pre_process_parsed_inv_taxes(parsed_inv)
        # Handle rounding:
        for line in parsed_inv.get("lines", []):
            line["qty"] = float_round(line["qty"], precision_digits=prec_uom)
            line["price_unit"] = float_round(
                line["price_unit"], precision_digits=prec_pp
            )
        parsed_inv_for_log = dict(parsed_inv)
        if "attachments" in parsed_inv_for_log:
            parsed_inv_for_log.pop("attachments")
        logger.debug("Result of invoice parsing parsed_inv=%s", parsed_inv_for_log)
        # the 'company' dict in parsed_inv is NOT used to auto-detect
        # the company, but to check that we are not importing an
        # invoice for another company by mistake
        # The advantage of doing the check here is that it will be run
        # in all scenarios (create/update/...), but it's not related
        # to invoice parsing...
        if (
            parsed_inv.get("company")
            and not config["test_enable"]
            and not self.env.context.get("edi_skip_company_check")
        ):
            self._check_company(parsed_inv["company"], parsed_inv["chatter_msg"])
        return parsed_inv

    @api.model
    def _pre_process_parsed_inv_taxes(self, parsed_inv):
        """Handle taxes in pre_processing parsed invoice."""
        # Handle the case where we import an invoice with VAT in a company that
        # cannot deduct VAT
        if self.company_cannot_refund_vat():
            parsed_inv["amount_tax"] = 0
            parsed_inv["amount_untaxed"] = parsed_inv["amount_total"]
            for line in parsed_inv.get("lines", []):
                if line.get("taxes"):
                    if len(line["taxes"]) > 1:
                        raise UserError(
                            _(
                                "You are importing an invoice in a company that "
                                "cannot deduct VAT and the imported invoice has "
                                "several VAT taxes on the same line (%s). We do "
                                "not support this scenario for the moment."
                            )
                            % line.get("name")
                        )
                    vat_rate = line["taxes"][0].get("amount")
                    if not float_is_zero(vat_rate, precision_digits=2):
                        line["price_unit"] = line["price_unit"] * (1 + vat_rate / 100.0)
                        line.pop("price_subtotal")
                        line["taxes"] = []
        # Rounding work
        for entry in ["amount_untaxed", "amount_total"]:
            parsed_inv[entry] = float_round(
                parsed_inv[entry], precision_rounding=parsed_inv["currency_rounding"]
            )

    @api.model
    def invoice_already_exists(self, commercial_partner, parsed_inv):
        company_id = self.env.context.get("force_company") or self.env.company.id
        existing_inv = self.env["account.move"].search(
            [
                ("company_id", "=", company_id),
                ("commercial_partner_id", "=", commercial_partner.id),
                ("move_type", "=", parsed_inv["type"]),
                ("ref", "=ilike", parsed_inv.get("invoice_number")),
            ],
            limit=1,
        )
        return existing_inv

    def get_parsed_invoice(self):
        """Hook to change the method of retrieval for the invoice data"""
        return self.parse_invoice(self.invoice_file, self.invoice_filename)

    def goto_partner_not_found(self, parsed_inv, error_message):
        """Hook designed to add an action when no partner is found
        For instance to propose to create the partner based on the partner_dict.
        """
        partner_dict = parsed_inv["partner"]
        vals = {
            "message": error_message,
            "state": "partner-not-found",
            "partner_vat": partner_dict.get("vat"),
        }
        if parsed_inv["partner"].get("country_code"):
            country = self.env["res.country"].search(
                [("code", "=", partner_dict["country_code"].upper().strip())], limit=1
            )
            if country:
                vals["partner_country_id"] = country.id
        self.write(vals)
        xmlid = "account_invoice_import.account_invoice_import_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["res_id"] = self.id
        return action

    def _prepare_partner_update(self):
        assert self.partner_vat
        assert not self.partner_id.parent_id
        vals = {}
        if self.partner_id.vat:
            if self.partner_id.vat != self.partner_vat:
                raise UserError(
                    _(
                        "The vendor to update '%s' already has a VAT number (%s) "
                        "which is different from the vendor VAT number "
                        "of the invoice (%s)."
                    )
                    % (
                        self.partner_id.display_name,
                        self.partner_id.vat,
                        self.partner_vat,
                    )
                )

        else:
            vals["vat"] = self.partner_vat
        if self.partner_country_id:
            if self.partner_id.country_id:
                if self.partner_id.country_id != self.partner_country_id:
                    raise UserError(
                        _(
                            "The vendor to update '%s' already has a country (%s) "
                            "which is different from the country of the vendor "
                            "of the invoice (%s)."
                        )
                        % (
                            self.partner_id.display_name,
                            self.partner_id.country_id.display_name,
                            self.partner_country_id.display_name,
                        )
                    )
            else:
                vals["country_id"] = self.partner_country_id.id
        return vals

    def update_partner_vat(self):
        """In the update process, we only take care of VAT and country code"""
        if not self.partner_id:
            raise UserError(_("You must select a vendor to update."))
        self.partner_id.write(self._prepare_partner_update())

    def update_partner_vat_show(self):
        self.update_partner_vat()
        action = {
            "name": self.partner_id.display_name,
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": self.partner_id.id,
            "view_mode": "form",
        }
        return action

    def update_partner_vat_continue(self):
        self.update_partner_vat()
        return self.import_invoice()

    def _prepare_new_partner_context(self, parsed_inv):
        partner_dict = parsed_inv["partner"]
        context = {
            "default_is_company": True,
            "default_supplier_rank": 1,
            "default_name": partner_dict.get("name"),
            "default_street_name": partner_dict.get("street"),
            "default_street2": partner_dict.get("street2"),
            "default_street3": partner_dict.get("street3"),
            "default_email": partner_dict.get("email"),
            "default_phone": partner_dict.get("phone"),
            "default_mobile": partner_dict.get("mobile"),
            "default_zip": partner_dict.get("zip"),
            "default_city": partner_dict.get("city"),
            "default_website": partner_dict.get("website"),
            "default_siren": partner_dict.get("siren"),
            "default_ref": partner_dict.get("ref"),
            "default_coc_registration_number": partner_dict.get(
                "coc_registration_number"
            ),
            "default_vat": self.partner_vat,
            "default_country_id": self.partner_country_id.id or False,
        }
        if (
            self.partner_country_id
            and partner_dict.get("state_code")
            and isinstance(partner_dict["state_code"], str)
        ):
            country_state = self.env["res.country.state"].search(
                [
                    ("code", "=", partner_dict["state_code"].upper().strip()),
                    ("country_id", "=", self.partner_country_id.id),
                ],
                limit=1,
            )
            if country_state:
                context["default_state_id"] = country_state.id
        return context

    def new_partner(self):
        parsed_inv = self.get_parsed_invoice()
        # we don't create a new partner, we just show a pre-filled partner form
        context = self._prepare_new_partner_context(parsed_inv)
        action = {
            "name": self.partner_id.display_name,
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "target": "current",
            "view_mode": "form",
            "context": context,
        }
        # After this, when you save the partner, the active_id field in the
        # URL is still the ID of the wizard. It will trigger an error if
        # you click on "0 invoice import configuration" right after:
        # Record does not exist or has been deleted.
        # (Record: res.partner(<ID wizard>,), User: 2)
        # If you have an idea on how to fix this problem, please tell me!
        return action

    def import_invoice(self):
        """Method called by the button of the wizard
        (import step AND config step)"""
        self.ensure_one()
        amo = self.env["account.move"]
        aiico = self.env["account.invoice.import.config"]
        company_id = self.env.context.get("force_company") or self.env.company.id
        parsed_inv = self.get_parsed_invoice()
        if not self.partner_id:
            if parsed_inv.get("partner"):
                try:
                    partner = self._match_partner(
                        parsed_inv["partner"], parsed_inv["chatter_msg"]
                    )
                except UserError as e:
                    return self.goto_partner_not_found(parsed_inv, e)
            else:
                partner = False
        else:
            partner = self.partner_id
        if partner:
            partner = partner.commercial_partner_id
            currency = self._match_currency(
                parsed_inv.get("currency"), parsed_inv["chatter_msg"]
            )
            parsed_inv["partner"]["recordset"] = partner
            parsed_inv["currency"]["recordset"] = currency
            wiz_vals = {
                "partner_id": partner.id,
                "invoice_type": parsed_inv["type"],
                "currency_id": currency.id,
                "amount_untaxed": parsed_inv["amount_untaxed"],
                "amount_total": parsed_inv["amount_total"],
            }

            existing_inv = self.invoice_already_exists(partner, parsed_inv)
            if existing_inv:
                self.message = _(
                    "This invoice already exists in Odoo. It's "
                    "Supplier Invoice Number is '%s' and it's Odoo number "
                    "is '%s'"
                ) % (parsed_inv.get("invoice_number"), existing_inv.name)
                self.state = "config"

            if self.import_config_id:  # button called from 'config' step
                wiz_vals["import_config_id"] = self.import_config_id.id
                import_config = self.import_config_id.convert_to_import_config()
            else:  # button called from 'import' step
                import_configs = aiico.search(
                    [("partner_id", "=", partner.id), ("company_id", "=", company_id)]
                )
                if not import_configs:
                    self.message = (
                        _("Missing Invoice Import Configuration on partner '%s'.")
                        % partner.display_name
                    )
                    self.state = "config"
                elif len(import_configs) == 1:
                    wiz_vals["import_config_id"] = import_configs.id
                    import_config = import_configs.convert_to_import_config()
                else:
                    logger.info(
                        "There are %d invoice import configs for partner %s",
                        len(import_configs),
                        partner.display_name,
                    )

            if not wiz_vals.get("import_config_id"):
                wiz_vals["state"] = "config"
                xmlid = "account_invoice_import.account_invoice_import_action"
                action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
                action["res_id"] = self.id
            else:
                draft_same_supplier_invs = amo.search(
                    [
                        ("commercial_partner_id", "=", partner.id),
                        ("move_type", "=", parsed_inv["type"]),
                        ("state", "=", "draft"),
                    ]
                )
                logger.debug("draft_same_supplier_invs=%s", draft_same_supplier_invs)
                if draft_same_supplier_invs:
                    wiz_vals["state"] = "update"
                    if len(draft_same_supplier_invs) == 1:
                        wiz_vals["invoice_id"] = draft_same_supplier_invs[0].id
                    xmlid = "account_invoice_import.account_invoice_import_action"
                    action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
                    action["res_id"] = self.id
                else:
                    action = self.create_invoice_action(
                        parsed_inv, import_config, _("Import Vendor Bill wizard")
                    )
            self.write(wiz_vals)
        else:
            action = self.create_invoice_action(
                parsed_inv, {}, _("Import Vendor Bill wizard")
            )
        return action

    def create_invoice_action_button(self):
        """If I call create_invoice_action()
        directly from the button, I get the context in parsed_inv"""
        return self.create_invoice_action(origin=_("Import Vendor Bill wizard"))

    def create_invoice_action(self, parsed_inv=None, import_config=None, origin=None):
        """parsed_inv is not a required argument"""
        self.ensure_one()
        if parsed_inv is None:
            parsed_inv = self.get_parsed_invoice()
        if import_config is None:
            assert self.import_config_id
            import_config = self.import_config_id.convert_to_import_config()
        invoice = self.create_invoice(parsed_inv, import_config, origin)
        xmlid = "account.action_move_in_invoice_type"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action.update(
            {
                "view_mode": "form,tree,kanban",
                "view_id": False,
                "views": False,
                "res_id": invoice.id,
            }
        )
        return action

    @api.model
    def create_invoice(self, parsed_inv, import_config=False, origin=None):
        amo = self.env["account.move"]
        parsed_inv = self.pre_process_parsed_inv(parsed_inv)
        vals = self._prepare_create_invoice_vals(parsed_inv, import_config)
        logger.debug("Invoice vals for creation: %s", vals)
        invoice = amo.create(vals)
        self.post_process_invoice(parsed_inv, invoice, import_config)
        logger.info("Invoice ID %d created", invoice.id)
        self.post_create_or_update(parsed_inv, invoice)
        invoice.message_post(
            body=_(
                "This invoice has been created automatically via file import. "
                "Origin: %s."
            )
            % (origin or _("unspecified"))
        )
        return invoice

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
        aiico = self.env["account.invoice.import.config"]
        if company_id is None:
            company_id = self.env.company.id
        logger.info(
            "Starting to import invoice file %s in company ID %d",
            invoice_filename,
            company_id,
        )
        parsed_inv = self.parse_invoice(
            invoice_file_b64, invoice_filename, email_from=email_from
        )
        partner = self._match_partner(
            parsed_inv["partner"], parsed_inv["chatter_msg"], raise_exception=False
        )
        if partner:
            partner = partner.commercial_partner_id
            # To avoid a second full _match_partner() inside create_invoice()
            parsed_inv["partner"]["recordset"] = partner
            existing_inv = self.invoice_already_exists(partner, parsed_inv)
            if existing_inv:
                logger.warning(
                    "This supplier invoice already exists "
                    "in Odoo (ID %d number %s supplier number %s)",
                    existing_inv.id,
                    existing_inv.name,
                    parsed_inv.get("invoice_number"),
                )
                return False
            import_configs = aiico.search(
                [("partner_id", "=", partner.id), ("company_id", "=", company_id)]
            )
            if not import_configs:
                logger.warning(
                    "Missing invoice import configuration "
                    "for partner '%s' in company ID %d.",
                    partner.display_name,
                    company_id,
                )
                import_config = {}
            elif len(import_configs) == 1:
                import_config = import_configs.convert_to_import_config()
            else:
                logger.info(
                    "There are %d invoice import configs for partner %s "
                    "in company ID %d. Using the first one '%s'",
                    len(import_configs),
                    partner.display_name,
                    company_id,
                    import_configs[0].name,
                )
                import_config = import_configs[0].convert_to_import_config()
        else:
            import_config = {}
        invoice = self.create_invoice(parsed_inv, import_config, origin)
        return invoice.id

    @api.model
    def _prepare_global_adjustment_line(self, diff_amount, invoice, import_config):
        amlo = self.env["account.move.line"]
        prec = invoice.currency_id.rounding
        sign = diff_amount > 0 and 1 or -1
        il_vals = {
            "name": _("Adjustment"),
            "quantity": sign,
            "price_unit": diff_amount * sign,
        }
        # no taxes nor product on such a global adjustment line
        if import_config["invoice_line_method"] == "nline_no_product":
            il_vals["account_id"] = import_config["account"].id
        elif import_config["invoice_line_method"] == "nline_static_product":
            account = amlo.get_invoice_line_account(
                invoice.type,
                import_config["product"],
                invoice.fiscal_position_id,
                invoice.company_id,
            )
            il_vals["account_id"] = account.id
        elif import_config["invoice_line_method"] == "nline_auto_product":
            res_cmp = float_compare(diff_amount, 0, precision_rounding=prec)
            company = invoice.company_id
            if res_cmp > 0:
                if not company.adjustment_debit_account_id:
                    raise UserError(
                        _(
                            "You must configure the 'Adjustment Debit Account' "
                            "on the Accounting Configuration page."
                        )
                    )
                il_vals["account_id"] = company.adjustment_debit_account_id.id
            else:
                if not company.adjustment_credit_account_id:
                    raise UserError(
                        _(
                            "You must configure the 'Adjustment Credit Account' "
                            "on the Accounting Configuration page."
                        )
                    )
                il_vals["account_id"] = company.adjustment_credit_account_id.id
        logger.debug("Prepared global adjustment invoice line %s", il_vals)
        return il_vals

    @api.model  # noqa: C901
    def post_process_invoice(self, parsed_inv, invoice, import_config):  # noqa: C901
        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
            return
        if not import_config:
            if invoice.commercial_partner_id:
                invoice.message_post(
                    body=_(
                        "<b>Missing Invoice Import Configuration</b> on partner "
                        "<a href=# data-oe-model=res.partner data-oe-id=%d>%s</a>: "
                        "the imported invoice is incomplete."
                    )
                    % (
                        invoice.commercial_partner_id.id,
                        invoice.commercial_partner_id.display_name,
                    )
                )
            return
        inv_cur = invoice.currency_id
        prec = inv_cur.rounding
        company_cur = invoice.company_id.currency_id
        account_prec = company_cur.rounding
        # If untaxed amount is wrong, create adjustment lines
        if (
            import_config["invoice_line_method"].startswith("nline")
            and invoice.invoice_line_ids
            and float_compare(
                parsed_inv["amount_untaxed"],
                invoice.amount_untaxed,
                precision_rounding=prec,
            )
        ):
            # Try to find the line that has a problem
            # TODO : on invoice creation, the lines are in the same
            # order, but not on invoice update...
            for i in range(len(parsed_inv["lines"])):
                if "price_subtotal" not in parsed_inv["lines"][i]:
                    continue
                if (
                    "display_type" in parsed_inv["lines"][i]
                ):  # if it is a line note, skip the checks
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
                    copy_dict = {
                        "name": _("Adjustment on %s") % iline.name,
                        "quantity": 1,
                        "price_unit": diff_amount,
                        "price_subtotal": False,
                        "debit": False,
                        "credit": False,
                        "amount_currency": False,
                        "price_total": False,
                    }
                    if import_config["invoice_line_method"] == "nline_auto_product":
                        copy_dict["product_id"] = False
                    # Add the adjustment line
                    iline.with_context(check_move_validity=False).copy(copy_dict)
                    invoice.with_context(
                        check_move_validity=False
                    )._recompute_dynamic_lines(recompute_all_taxes=True)
                    invoice._check_balanced()
                    logger.info("Adjustment invoice line created")
        # Fallback: create global adjustment line
        if float_compare(
            parsed_inv["amount_untaxed"],
            invoice.amount_untaxed,
            precision_rounding=prec,
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
            il_vals["move_id"] = invoice.id
            mline = (
                self.env["account.move.line"]
                .with_context(check_move_validity=False)
                .create(il_vals)
            )
            invoice.with_context(check_move_validity=False)._recompute_dynamic_lines(
                recompute_all_taxes=True
            )
            invoice._check_balanced()
            logger.info("Global adjustment invoice line created ID %d", mline.id)
        assert not float_compare(
            parsed_inv["amount_untaxed"],
            invoice.amount_untaxed,
            precision_rounding=prec,
        )
        # Force tax amount if necessary
        if float_compare(
            invoice.amount_total, parsed_inv["amount_total"], precision_rounding=prec
        ):
            diff_tax_amount = parsed_inv["amount_total"] - invoice.amount_total

            has_tax_line = False
            for mline in invoice.line_ids:
                # select first tax line
                if mline.tax_line_id and not company_cur.is_zero(mline.amount_currency):
                    has_tax_line = True
                    if mline.currency_id.compare_amounts(mline.amount_currency, 0) >= 0:
                        new_amount_currency = inv_cur.round(
                            mline.amount_currency + diff_tax_amount
                        )
                    else:
                        new_amount_currency = inv_cur.round(
                            mline.amount_currency - diff_tax_amount
                        )
                    invoice.message_post(
                        body=_(
                            "The <b>tax amount</b> for tax %s has been <b>forced</b> "
                            "to %s (amount computed by Odoo was: %s)."
                        )
                        % (
                            mline.tax_line_id.display_name,
                            format_amount(
                                self.env, new_amount_currency, invoice.currency_id
                            ),
                            format_amount(
                                self.env, mline.amount_currency, invoice.currency_id
                            ),
                        )
                    )
                    new_balance = invoice.currency_id._convert(
                        new_amount_currency,
                        invoice.company_id.currency_id,
                        invoice.company_id,
                        invoice.date,
                    )
                    vals = {"amount_currency": new_amount_currency}
                    if (
                        float_compare(new_balance, 0, precision_rounding=account_prec)
                        > 0
                    ):
                        vals["debit"] = new_balance
                        vals["credit"] = 0
                    else:
                        vals["debit"] = 0
                        vals["credit"] = new_balance * -1
                    logger.info("Force VAT amount with diff=%s", diff_tax_amount)
                    mline.with_context(check_move_validity=False).write(vals)
                    invoice.with_context(
                        check_move_validity=False
                    )._recompute_dynamic_lines()
                    invoice._check_balanced()
                    break
            if not has_tax_line:
                raise UserError(
                    _(
                        "The total amount is different from the untaxed amount, "
                        "but no tax has been configured !"
                    )
                )
        assert not float_compare(
            parsed_inv["amount_total"],
            invoice.amount_total,
            precision_rounding=prec,
        )

    def update_invoice_lines(self, parsed_inv, invoice, seller):
        chatter = parsed_inv["chatter_msg"]
        amlo = self.env["account.move.line"]
        qty_prec = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        existing_lines = []
        for eline in invoice.invoice_line_ids:
            price_unit = 0.0
            if not float_is_zero(eline.quantity, precision_digits=qty_prec):
                price_unit = eline.price_subtotal / float(eline.quantity)
            existing_lines.append(
                {
                    "product": eline.product_id or False,
                    "name": eline.name,
                    "qty": eline.quantity,
                    "uom": eline.product_uom_id,
                    "line": eline,
                    "price_unit": price_unit,
                }
            )
        compare_res = self.compare_lines(
            existing_lines, parsed_inv["lines"], chatter, seller=seller
        )
        if not compare_res:
            return
        for eline, cdict in list(compare_res["to_update"].items()):
            write_vals = {}
            if cdict.get("qty"):
                chatter.append(
                    _(
                        "The quantity has been updated on the invoice line "
                        "with product '%s' from %s to %s %s"
                    )
                    % (
                        eline.product_id.display_name,
                        cdict["qty"][0],
                        cdict["qty"][1],
                        eline.product_uom_id.name,
                    )
                )
                write_vals["quantity"] = cdict["qty"][1]
            if cdict.get("price_unit"):
                chatter.append(
                    _(
                        "The unit price has been updated on the invoice "
                        "line with product '%s' from %s to %s %s"
                    )
                    % (
                        eline.product_id.display_name,
                        eline.price_unit,
                        cdict["price_unit"][1],  # TODO fix
                        invoice.currency_id.name,
                    )
                )
                write_vals["price_unit"] = cdict["price_unit"][1]
            if write_vals:
                eline.write(write_vals)
        if compare_res["to_remove"]:
            to_remove_label = [
                "{} {} x {}".format(
                    line.quantity, line.product_uom_id.name, line.product_id.name
                )
                for line in compare_res["to_remove"]
            ]
            chatter.append(
                _("%d invoice line(s) deleted: %s")
                % (len(compare_res["to_remove"]), ", ".join(to_remove_label))
            )
            compare_res["to_remove"].unlink()
        if compare_res["to_add"]:
            to_create_label = []
            for add in compare_res["to_add"]:
                line_vals = self._prepare_create_invoice_line(
                    add["product"], add["uom"], add["import_line"], invoice
                )
                new_line = amlo.create(line_vals)
                to_create_label.append(
                    "%s %s x %s"
                    % (new_line.quantity, new_line.product_uom_id.name, new_line.name)
                )
            chatter.append(
                _("%d new invoice line(s) created: %s")
                % (len(compare_res["to_add"]), ", ".join(to_create_label))
            )
        invoice.compute_taxes()
        return True

    @api.model
    def _prepare_create_invoice_line(self, product, uom, import_line, invoice):
        new_line = self.env["account.move.line"].new(
            {"move_id": invoice, "qty": import_line["qty"], "product_id": product}
        )
        new_line._onchange_product_id()
        vals = {
            f: new_line._fields[f].convert_to_write(new_line[f], new_line)
            for f in new_line._cache
        }
        vals.update(
            {
                "product_id": product.id,
                "price_unit": import_line.get("price_unit"),
                "quantity": import_line["qty"],
                "move_id": invoice.id,
            }
        )
        return vals

    @api.model
    def _prepare_update_invoice_vals(self, parsed_inv, invoice):
        vals = {
            "ref": parsed_inv.get("invoice_number"),
            "invoice_date": parsed_inv.get("date"),
        }
        if parsed_inv.get("date_due"):
            vals["invoice_date_due"] = parsed_inv["date_due"]
        if parsed_inv.get("iban"):
            company = invoice.company_id
            partner_bank = self._match_partner_bank(
                invoice.commercial_partner_id,
                parsed_inv["iban"],
                parsed_inv.get("bic"),
                parsed_inv["chatter_msg"],
                create_if_not_found=company.invoice_import_create_bank_account,
            )
            if partner_bank:
                vals["partner_bank_id"] = partner_bank.id
        return vals

    def update_invoice(self):
        """Called by the button of the wizard (step 'update-from-invoice')"""
        self.ensure_one()
        invoice = self.invoice_id
        if not invoice:
            raise UserError(_("You must select a supplier invoice or refund to update"))
        parsed_inv = self.get_parsed_invoice()
        if self.partner_id:
            # True if state='update' ; False when state='update-from-invoice'
            parsed_inv["partner"]["recordset"] = self.partner_id
        partner = self._match_partner(
            parsed_inv["partner"], parsed_inv["chatter_msg"], partner_type="supplier"
        )
        partner = partner.commercial_partner_id
        if partner != invoice.commercial_partner_id:
            raise UserError(
                _(
                    "The supplier of the imported invoice (%s) is different from "
                    "the supplier of the invoice to update (%s)."
                )
                % (partner.name, invoice.commercial_partner_id.name)
            )
        if not self.import_config_id:
            raise UserError(_("You must select an Invoice Import Configuration."))
        import_config = self.import_config_id.convert_to_import_config()
        currency = self._match_currency(
            parsed_inv.get("currency"), parsed_inv["chatter_msg"]
        )
        if currency != invoice.currency_id:
            raise UserError(
                _(
                    "The currency of the imported invoice (%s) is different from "
                    "the currency of the existing invoice (%s)"
                )
                % (currency.name, invoice.currency_id.name)
            )
        vals = self._prepare_update_invoice_vals(parsed_inv, invoice)
        logger.debug("Updating supplier invoice with vals=%s", vals)
        self.invoice_id.write(vals)
        if (
            parsed_inv.get("lines")
            and import_config["invoice_line_method"] == "nline_auto_product"
        ):
            self.update_invoice_lines(parsed_inv, invoice, partner)
        self.post_process_invoice(parsed_inv, invoice, import_config)
        if import_config["account_analytic"]:
            invoice.invoice_line_ids.write(
                {"analytic_account_id": import_config["account_analytic"].id}
            )
        self.post_create_or_update(parsed_inv, invoice)
        logger.info(
            "Supplier invoice ID %d updated via import of file %s",
            invoice.id,
            self.invoice_filename,
        )
        invoice.message_post(
            body=_(
                "This invoice has been updated automatically via the import "
                "of file %s"
            )
            % self.invoice_filename
        )
        xmlid = "account.action_move_in_invoice_type"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action.update(
            {
                "view_mode": "form,tree,kanban",
                "views": False,
                "view_id": False,
                "res_id": invoice.id,
            }
        )
        return action

    def xpath_to_dict_helper(self, xml_root, xpath_dict, namespaces):
        for key, value in xpath_dict.items():
            if isinstance(value, list):
                isdate = isfloat = False
                if "date" in key:
                    isdate = True
                elif "amount" in key:
                    isfloat = True
                xpath_dict[key] = self.multi_xpath_helper(
                    xml_root, value, namespaces, isdate=isdate, isfloat=isfloat
                )
                if not xpath_dict[key]:
                    logger.debug("pb")
            elif isinstance(value, dict):
                xpath_dict[key] = self.xpath_to_dict_helper(xml_root, value, namespaces)
        return xpath_dict
        # TODO: think about blocking required fields

    def multi_xpath_helper(
        self, xml_root, xpath_list, namespaces, isdate=False, isfloat=False
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
                        raise UserError(_("Only the date format 102 is supported "))
                    date_dt = datetime.strptime(xpath_res[0].text, "%Y%m%d")
                    date_str = fields.Date.to_string(date_dt)
                    return date_str
                elif isfloat:
                    res_float = float(xpath_res[0].text)
                    return res_float
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
    def get_precision_rounding_from_currency_helper(self, parsed_inv):
        try:
            currency = self._match_currency(parsed_inv["currency"], [])
            precision_rounding = currency.rounding
        except Exception:
            precision_rounding = self.env.company.currency_id.rounding
        parsed_inv["currency_rounding"] = precision_rounding
        return precision_rounding

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Process the message data from a fetchmail configuration

        The caller expects us to create a record so we always return an empty
        one even though the actual result is the imported invoice, if the
        message content allows it.
        """
        # TODO: split this method into smaller ones
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
                origin = _("email sent by <b>%s</b> on %s with subject <b>%s</b>") % (
                    msg_dict.get("email_from") and html.escape(msg_dict["email_from"]),
                    msg_dict.get("date"),
                    msg_dict.get("subject") and html.escape(msg_dict["subject"]),
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
