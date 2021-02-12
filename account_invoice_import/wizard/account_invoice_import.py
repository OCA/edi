# Copyright 2015-2018 Akretion France (http://www.akretion.com/)
# Copyright 2020 Therp BV (https://therp.nl)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import mimetypes
from datetime import datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_compare, float_is_zero, float_round

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _name = "account.invoice.import"
    _description = "Wizard to import supplier invoices/refunds"

    invoice_file = fields.Binary(string="PDF or XML Invoice", required=True)
    invoice_filename = fields.Char(string="Filename")
    state = fields.Selection(
        [
            ("import", "Import"),
            ("config", "Select Invoice Import Configuration"),
            ("update", "Update"),
            ("update-from-invoice", "Update From Invoice"),
        ],
        default="import",
    )
    partner_id = fields.Many2one("res.partner", string="Supplier", readonly=True)
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
                    ("company_id", "=", self.env.user.company_id.id),
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
        the same kind of logic as the account_bank_statement_import_*
        modules"""
        bdio = self.env["business.document.import"]
        xml_files_dict = bdio.get_xml_files_from_pdf(file_data)
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            parsed_inv = self.parse_xml_invoice(xml_root)
            if parsed_inv:
                return parsed_inv
        parsed_inv = self.fallback_parse_pdf_invoice(file_data)
        if not parsed_inv:
            raise UserError(
                _(
                    "This type of PDF invoice is not supported. Did you install "
                    "the module to support this type of file?"
                )
            )
        return parsed_inv

    def fallback_parse_pdf_invoice(self, file_data):
        """Designed to be inherited by the module
        account_invoice_import_invoice2data, to be sure the invoice2data
        technique is used after the electronic invoice modules such as
        account_invoice_import_zugferd
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
        # 'currency': {
        #    'iso': 'EUR',
        #    'currency_symbol': u'€',  # The one or the other
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

    def company_cannot_refund_vat(self):
        company_id = (
            self.env.context.get("force_company") or self.env.user.company_id.id
        )
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
    def parse_invoice(self, invoice_file_b64, invoice_filename):
        assert invoice_file_b64, "No invoice file"
        logger.info("Starting to import invoice %s", invoice_filename)
        file_data = base64.b64decode(invoice_file_b64)
        filetype = mimetypes.guess_type(invoice_filename)
        logger.debug("Invoice mimetype: %s", filetype)
        if filetype and filetype[0] in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(file_data)
            except Exception as e:
                raise UserError(_("This XML file is not XML-compliant. Error: %s") % e)
            pretty_xml_string = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_string)
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
        # FIXME binary is not Serializable
        # if "attachments" not in parsed_inv:
        #     parsed_inv["attachments"] = {}
        # parsed_inv["attachments"][invoice_filename] = invoice_file_b64
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
        prec_ac = self.env["decimal.precision"].precision_get("Account")
        prec_pp = self.env["decimal.precision"].precision_get("Product Price")
        prec_uom = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
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
            and float_compare(parsed_inv["amount_total"], 0, precision_digits=prec_ac)
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
        logger.debug("Result of invoice parsing parsed_inv=%s", parsed_inv)
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
            self.env["business.document.import"]._check_company(
                parsed_inv["company"], parsed_inv["chatter_msg"]
            )
        return parsed_inv

    @api.model
    def _pre_process_parsed_inv_taxes(self, parsed_inv):
        """Handle taxes in pre_processing parsed invoice."""
        # Handle the case where we import an invoice with VAT in a company that
        # cannot deduct VAT
        prec_ac = self.env["decimal.precision"].precision_get("Account")
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
            parsed_inv[entry] = float_round(parsed_inv[entry], precision_digits=prec_ac)

    @api.model
    def invoice_already_exists(self, commercial_partner, parsed_inv):
        company_id = (
            self.env.context.get("force_company") or self.env.user.company_id.id
        )
        existing_inv = self.env["account.move"].search(
            [
                ("company_id", "=", company_id),
                ("commercial_partner_id", "=", commercial_partner.id),
                ("type", "=", parsed_inv["type"]),
                ("invoice_payment_ref", "=ilike", parsed_inv.get("invoice_number")),
            ],
            limit=1,
        )
        return existing_inv

    def get_parsed_invoice(self):
        """Hook to change the method of retrieval for the invoice data"""
        return self.parse_invoice(self.invoice_file, self.invoice_filename)

    def _hook_no_partner_found(self, partner_dict):
        """Hook designed to add an action when no partner is found
        For instance to propose to create the partner based on the partner_dict.
        """
        return False

    def import_invoice(self):
        """Method called by the button of the wizard
        (import step AND config step)"""
        self.ensure_one()
        aio = self.env["account.move"]
        aiico = self.env["account.invoice.import.config"]
        bdio = self.env["business.document.import"]
        iaao = self.env["ir.actions.act_window"]
        company_id = (
            self.env.context.get("force_company") or self.env.user.company_id.id
        )
        parsed_inv = self.get_parsed_invoice()
        if not self.partner_id:
            try:
                partner = bdio._match_partner(
                    parsed_inv["partner"], parsed_inv["chatter_msg"]
                )
            except UserError as e:
                action = self._hook_no_partner_found(parsed_inv["partner"])
                if action:
                    return action
                raise e
        else:
            partner = self.partner_id
        partner = partner.commercial_partner_id
        currency = bdio._match_currency(
            parsed_inv.get("currency"), parsed_inv["chatter_msg"]
        )
        wiz_vals = {
            "partner_id": partner.id,
            "invoice_type": parsed_inv["type"],
            "currency_id": currency.id,
            "amount_untaxed": parsed_inv["amount_untaxed"],
            "amount_total": parsed_inv["amount_total"],
        }

        existing_inv = self.invoice_already_exists(partner, parsed_inv)
        if existing_inv:
            raise UserError(
                _(
                    "This invoice already exists in Odoo. It's "
                    "Supplier Invoice Number is '%s' and it's Odoo number "
                    "is '%s'"
                )
                % (parsed_inv.get("invoice_number"), existing_inv.name)
            )

        if self.import_config_id:  # button called from 'config' step
            wiz_vals["import_config_id"] = self.import_config_id.id
        else:  # button called from 'import' step
            import_configs = aiico.search(
                [("partner_id", "=", partner.id), ("company_id", "=", company_id)]
            )
            if not import_configs:
                raise UserError(
                    _("Missing Invoice Import Configuration on partner '%s'.")
                    % partner.display_name
                )
            elif len(import_configs) == 1:
                wiz_vals["import_config_id"] = import_configs.id
            else:
                logger.info(
                    "There are %d invoice import configs for partner %s",
                    len(import_configs),
                    partner.display_name,
                )

        if not wiz_vals.get("import_config_id"):
            wiz_vals["state"] = "config"
            action = iaao.for_xml_id(
                "account_invoice_import", "account_invoice_import_action"
            )
            action["res_id"] = self.id
        else:
            draft_same_supplier_invs = aio.search(
                [
                    ("commercial_partner_id", "=", partner.id),
                    ("type", "=", parsed_inv["type"]),
                    ("state", "=", "draft"),
                ]
            )
            logger.debug("draft_same_supplier_invs=%s", draft_same_supplier_invs)
            if draft_same_supplier_invs:
                wiz_vals["state"] = "update"
                if len(draft_same_supplier_invs) == 1:
                    wiz_vals["invoice_id"] = draft_same_supplier_invs[0].id
                action = iaao.for_xml_id(
                    "account_invoice_import", "account_invoice_import_action"
                )
                action["res_id"] = self.id
            else:
                self.write(wiz_vals)
                return self.create_invoice_action(parsed_inv)
        self.write(wiz_vals)
        return action

    def create_invoice_action_button(self):
        """Workaround for a v10 bug: if I call create_invoice_action()
        directly from the button, I get the context in parsed_inv"""
        return self.create_invoice_action()

    def _exchange_record_vals(self, parsed_inv):
        vals = {
            "edi_exchange_state": "input_received",
            "exchange_file": base64.b64encode(json.dumps(parsed_inv).encode("UTF-8")),
            "exchange_filename": "account.invoice.import.json",
            "model": self._name,
            "res_id": self.id,
        }
        return vals

    def create_invoice_action(self, parsed_inv=None):
        """parsed_inv is not a required argument"""
        self.ensure_one()
        iaao = self.env["ir.actions.act_window"]
        if parsed_inv is None:
            parsed_inv = self.get_parsed_invoice()
        exchange_record = self.import_config_id.backend_id.create_record(
            "account.invoice.import", self._exchange_record_vals(parsed_inv)
        )
        self.import_config_id.backend_id.with_context(
            _edi_receive_break_on_error=True
        ).exchange_process(exchange_record)
        invoice = exchange_record.record
        invoice.message_post(
            body=_("This invoice has been created automatically via file import")
        )
        action = iaao.for_xml_id("account", "action_move_in_invoice_type")
        action.update({"view_mode": "form,tree,calendar,graph", "res_id": invoice.id})
        return action

    @api.model
    def create_invoice(self, parsed_inv):
        exchange_record = self.import_config_id.backend_id.create_record(
            "account.invoice.import", self._exchange_record_vals(parsed_inv)
        )
        self.import_config_id.backend_id.exchange_process(exchange_record)
        # State procceded with cron cannot check synchronously
        if exchange_record.edi_exchange_state != "input_processed":
            raise UserError(_("Something wrong happened when processing the invoice"))
        return exchange_record.record

    def _update_invoice(self, parsed_inv):
        if self.partner_id:
            # True if state='update' ; False when state='update-from-invoice'
            parsed_inv["partner"]["id"] = self.partner_id.id
        exchange_record = self.import_config_id.backend_id.create_record(
            "account.invoice.import", self._exchange_record_vals(parsed_inv)
        )
        self.import_config_id.backend_id.with_context(
            _edi_receive_break_on_error=True
        ).exchange_process(exchange_record)
        invoice = exchange_record.record
        invoice.message_post(
            body=_(
                "This invoice has been updated automatically via the import "
                "of file %s"
            )
            % self.invoice_filename
        )
        return invoice

    def update_invoice(self):
        """Called by the button of the wizard (step 'update-from-invoice')"""
        self.ensure_one()
        iaao = self.env["ir.actions.act_window"]
        invoice = self.invoice_id
        if not invoice:
            raise UserError(_("You must select a supplier invoice or refund to update"))
        if not self.import_config_id:
            raise UserError(_("You must select an Invoice Import Configuration."))
        parsed_inv = self.get_parsed_invoice()
        invoice = self._update_invoice(parsed_inv)
        action = iaao.for_xml_id("account", "action_invoice_tree2")
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
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
    def message_new(self, msg_dict, custom_values=None):
        logger.info(
            "New email received associated with account.invoice.import: "
            "From: %s, Subject: %s, Date: %s, Message ID: %s. Executing "
            "with user %s ID %d",
            msg_dict.get("email_from"),
            msg_dict.get("subject"),
            msg_dict.get("date"),
            msg_dict.get("message_id"),
            self.env.user.name,
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
                            "Matched with %s: importing invoices in company " "ID %d",
                            company_dest_email,
                            company_id,
                        )
                        break
            if not company_id:
                logger.error(
                    "Invoice import mail gateway in multi-company setup: "
                    "invoice_import_email of the companies of this DB was "
                    "not found as destination of this email (to: %s, cc: %s). "
                    "Ignoring this email.",
                    msg_dict["email_to"],
                    msg_dict["cc"],
                )
                return
        else:  # mono-company setup
            company_id = all_companies[0]["id"]

        self = self.with_context(force_company=company_id)
        aiico = self.env["account.invoice.import.config"]
        bdio = self.env["business.document.import"]
        i = 0
        if msg_dict.get("attachments"):
            i += 1
            for attach in msg_dict["attachments"]:
                logger.info(
                    "Attachment %d: %s. Trying to import it as an invoice",
                    i,
                    attach.fname,
                )
                parsed_inv = self.parse_invoice(
                    base64.b64encode(attach.content), attach.fname
                )
                partner = bdio._match_partner(
                    parsed_inv["partner"], parsed_inv["chatter_msg"]
                )

                existing_inv = self.invoice_already_exists(partner, parsed_inv)
                if existing_inv:
                    logger.warning(
                        "Mail import: this supplier invoice already exists "
                        "in Odoo (ID %d number %s supplier number %s)",
                        existing_inv.id,
                        existing_inv.name,
                        parsed_inv.get("invoice_number"),
                    )
                    continue
                import_configs = aiico.search(
                    [("partner_id", "=", partner.id), ("company_id", "=", company_id)]
                )
                if not import_configs:
                    logger.warning(
                        "Mail import: missing Invoice Import Configuration "
                        "for partner '%s'.",
                        partner.display_name,
                    )
                    continue
                elif len(import_configs) == 1:
                    import_config = import_configs.convert_to_import_config()
                else:
                    logger.info(
                        "There are %d invoice import configs for partner %s. "
                        "Using the first one '%s''",
                        len(import_configs),
                        partner.display_name,
                        import_configs[0].name,
                    )
                    import_config = import_configs[0].convert_to_import_config()
                invoice = self.create_invoice(parsed_inv, import_config)
                logger.info("Invoice ID %d created from email", invoice.id)
                invoice.message_post(
                    body=_(
                        "Invoice successfully imported from email sent by "
                        "<b>%s</b> on %s with subject <i>%s</i>."
                    )
                    % (
                        msg_dict.get("email_from"),
                        msg_dict.get("date"),
                        msg_dict.get("subject"),
                    )
                )
        else:
            logger.info("The email has no attachments, skipped.")
