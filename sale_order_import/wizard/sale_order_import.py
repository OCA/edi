# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from base64 import b64decode, b64encode

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_compare, float_is_zero

logger = logging.getLogger(__name__)


class SaleOrderImport(models.TransientModel):
    _name = "sale.order.import"
    _description = "Sale Order Import from Files"

    state = fields.Selection(
        [("import", "Import"), ("update", "Update")], string="State", default="import"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", domain=[("customer", "=", True)]
    )
    csv_import = fields.Boolean(default=False, readonly=True)
    order_file = fields.Binary(
        string="Request for Quotation or Order",
        required=True,
        help="Upload a Request for Quotation or an Order file. Supported "
        "formats: CSV, XML and PDF (PDF with an embeded XML file).",
    )
    order_filename = fields.Char(string="Filename")
    doc_type = fields.Selection(
        [("rfq", "Request For Quotation"), ("order", "Sale Order")],
        string="Document Type",
        readonly=True,
    )
    price_source = fields.Selection(
        [("pricelist", "Pricelist"), ("order", "Customer Order")],
        string="Apply Prices From",
    )
    # for state = update
    commercial_partner_id = fields.Many2one(
        "res.partner", string="Commercial Entity", readonly=True
    )
    partner_shipping_id = fields.Many2one(
        "res.partner", string="Shipping Address", readonly=True
    )
    sale_id = fields.Many2one("sale.order", string="Quotation to Update")

    @api.onchange("order_file")
    def order_file_change(self):
        if self.order_filename and self.order_file:
            filetype = mimetypes.guess_type(self.order_filename)
            logger.debug("Order file mimetype: %s", filetype)
            if filetype and filetype[0] in ("text/csv", "text/plain"):
                self.csv_import = True
                self.doc_type = False
            elif filetype and filetype[0] in ["application/xml", "text/xml"]:
                self.csv_import = False
                try:
                    xml_root = etree.fromstring(b64decode(self.order_file))
                except etree.XMLSyntaxError:
                    raise UserError(_("This XML file is not XML-compliant"))
                doc_type = self.parse_xml_order(xml_root, detect_doc_type=True)
                self.doc_type = doc_type
            elif filetype and filetype[0] == "application/pdf":
                self.csv_import = False
                doc_type = self.parse_pdf_order(
                    b64decode(self.order_file), detect_doc_type=True
                )
                self.doc_type = doc_type
            else:
                return {
                    "warning": {
                        "title": _("Unsupported file format"),
                        "message": _(
                            "This file '%s' is not recognised as a CSV, XML nor "
                            "PDF file. Please check the file and it's "
                            "extension."
                        )
                        % self.order_filename,
                    }
                }
        else:
            self.csv_import = False
            self.doc_type = False

    @api.model
    def get_xml_doc_type(self, xml_root):
        raise UserError

    @api.model
    def parse_xml_order(self, xml_root, detect_doc_type=False):
        raise UserError(
            _(
                "This type of XML RFQ/order is not supported. Did you install "
                "the module to support this XML format?"
            )
        )

    @api.model
    def parse_csv_order(self, order_file, partner):
        assert partner, "missing partner"
        raise UserError(
            _(
                "This type of CSV order is not supported. Did you install "
                "the module to support CSV orders?"
            )
        )

    @api.model
    def parse_pdf_order(self, order_file, detect_doc_type=False):
        """
        Get PDF attachments, filter on XML files and call import_order_xml
        """
        xml_files_dict = self.get_xml_files_from_pdf(order_file)
        if not xml_files_dict:
            raise UserError(_("There are no embedded XML file in this PDF file."))
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_order = self.parse_xml_order(
                    xml_root, detect_doc_type=detect_doc_type
                )
                return parsed_order
            except (etree.LxmlError, UserError):
                continue
        raise UserError(
            _(
                "This type of XML RFQ/order is not supported. Did you install "
                "the module to support this XML format?"
            )
        )

    # Format of parsed_order
    # {
    # 'partner': {
    #     'vat': 'FR25499247138',
    #     'name': 'Camptocamp',
    #     'email': 'luc@camptocamp.com',
    #     },
    # 'ship_to': {
    #    'partner': partner_dict,
    #    'address': {
    #       'country_code': 'FR',
    #       'state_code': False,
    #       'zip': False,
    #       },
    # 'company': {'vat': 'FR12123456789'},  # Only used to check we are not
    #                                       # importing the order in the
    #                                       # wrong company by mistake
    # 'date': '2016-08-16',  # order date
    # 'order_ref': 'PO1242',  # Customer PO number
    # 'currency': {'iso': 'EUR', 'symbol': u'€'},
    # 'incoterm': 'EXW',
    # 'note': 'order notes of the customer',
    # 'chatter_msg': ['msg1', 'msg2']
    # 'lines': [{
    #           'product': {
    #                'code': 'EA7821',
    #                'ean13': '2100002000003',
    #                },
    #           'qty': 2.5,
    #           'uom': {'unece_code': 'C62'},
    #           'price_unit': 12.42,  # without taxes
    # 'doc_type': 'rfq' or 'order',
    #    }]

    @api.model
    def _prepare_order(self, parsed_order, price_source):
        soo = self.env["sale.order"]
        bdio = self.env["business.document.import"]
        partner = bdio._match_partner(
            parsed_order["partner"],
            parsed_order["chatter_msg"],
            partner_type="customer",
        )
        currency = bdio._match_currency(
            parsed_order.get("currency"), parsed_order["chatter_msg"]
        )
        if partner.property_product_pricelist.currency_id != currency:
            raise UserError(
                _(
                    "The customer '%s' has a pricelist '%s' but the "
                    "currency of this order is '%s'."
                )
                % (
                    partner.display_name,
                    partner.property_product_pricelist.display_name,
                    currency.name,
                )
            )
        if parsed_order.get("order_ref"):
            commercial_partner = partner.commercial_partner_id
            existing_orders = soo.search(
                [
                    ("client_order_ref", "=", parsed_order["order_ref"]),
                    ("commercial_partner_id", "=", commercial_partner.id),
                    ("state", "!=", "cancel"),
                ]
            )
            if existing_orders:
                raise UserError(
                    _(
                        "An order of customer '%s' with reference '%s' "
                        "already exists: %s (state: %s)"
                    )
                    % (
                        partner.display_name,
                        parsed_order["order_ref"],
                        existing_orders[0].name,
                        existing_orders[0].state,
                    )
                )

        so_vals = {
            "partner_id": partner.id,
            "client_order_ref": parsed_order.get("order_ref"),
        }
        so_vals = soo.play_onchanges(so_vals, ["partner_id"])
        so_vals["order_line"] = []
        if parsed_order.get("ship_to"):
            shipping_partner = bdio._match_shipping_partner(
                parsed_order["ship_to"], partner, parsed_order["chatter_msg"]
            )
            so_vals["partner_shipping_id"] = shipping_partner.id
        if parsed_order.get("invoice_to"):
            invoicing_partner = bdio._match_partner(
                parsed_order["partner"], parsed_order["chatter_msg"], partner_type=""
            )
            so_vals["partner_invoice_id"] = invoicing_partner.id
        if parsed_order.get("date"):
            so_vals["date_order"] = parsed_order["date"]
        for line in parsed_order["lines"]:
            # partner=False because we don't want to use product.supplierinfo
            product = bdio._match_product(
                line["product"], parsed_order["chatter_msg"], seller=False
            )
            uom = bdio._match_uom(line.get("uom"), parsed_order["chatter_msg"], product)
            line_vals = self._prepare_create_order_line(
                product, uom, so_vals, line, price_source
            )
            so_vals["order_line"].append((0, 0, line_vals))
        return so_vals

    @api.model
    def create_order(self, parsed_order, price_source, order_filename=None):
        soo = self.env["sale.order"]
        bdio = self.env["business.document.import"]
        so_vals = self._prepare_order(parsed_order, price_source)
        order = soo.create(so_vals)
        bdio.post_create_or_update(parsed_order, order, doc_filename=order_filename)
        logger.info("Sale Order ID %d created", order.id)
        return order

    @api.model
    def create_order_ws(self, parsed_order, price_source, order_filename=None):
        """Same method as create_order() but callable via JSON-RPC
        webservice. Returns an ID to avoid this error:
        TypeError: sale.order(15,) is not JSON serializable"""
        order = self.create_order(
            parsed_order, price_source, order_filename=order_filename
        )
        return order.id

    @api.model
    def parse_order(self, order_file, order_filename, partner=False):
        assert order_file, "Missing order file"
        assert order_filename, "Missing order filename"
        filetype = mimetypes.guess_type(order_filename)[0]
        logger.debug("Order file mimetype: %s", filetype)
        if filetype in ("text/csv", "text/plain"):
            if not partner:
                raise UserError(_("Missing customer"))
            parsed_order = self.parse_csv_order(order_file, partner)
        elif filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(order_file)
            except etree.LxmlError:
                raise UserError(_("This XML file is not XML-compliant"))
            pretty_xml_string = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_string)
            parsed_order = self.parse_xml_order(xml_root)
        elif filetype == "application/pdf":
            parsed_order = self.parse_pdf_order(order_file)
        else:
            raise UserError(
                _(
                    "This file '%s' is not recognised as a CSV, XML nor PDF file. "
                    "Please check the file and it's extension."
                )
                % order_filename
            )
        logger.debug("Result of order parsing: %s", parsed_order)
        if "attachments" not in parsed_order:
            parsed_order["attachments"] = {}
        parsed_order["attachments"][order_filename] = b64encode(order_file)
        if "chatter_msg" not in parsed_order:
            parsed_order["chatter_msg"] = []
        if (
            parsed_order.get("company")
            and not config["test_enable"]
            and not self._context.get("edi_skip_company_check")
        ):
            self.env["business.document.import"]._check_company(
                parsed_order["company"], parsed_order["chatter_msg"]
            )
        return parsed_order

    def import_order_button(self):
        self.ensure_one()
        bdio = self.env["business.document.import"]
        order_file_decoded = b64decode(self.order_file)
        parsed_order = self.parse_order(
            order_file_decoded, self.order_filename, self.partner_id
        )
        if not parsed_order.get("lines"):
            raise UserError(_("This order doesn't have any line !"))
        partner = bdio._match_partner(
            parsed_order["partner"], [], partner_type="customer"
        )
        commercial_partner = partner.commercial_partner_id
        partner_shipping_id = False
        if parsed_order.get("ship_to"):
            partner_shipping_id = bdio._match_shipping_partner(
                parsed_order["ship_to"], partner, []
            ).id
        existing_quotations = self.env["sale.order"].search(
            [
                ("commercial_partner_id", "=", commercial_partner.id),
                ("state", "in", ("draft", "sent")),
                ("client_order_ref", "=", parsed_order.get("order_ref")),
            ]
        )
        if existing_quotations:
            default_sale_id = False
            if len(existing_quotations) == 1:
                default_sale_id = existing_quotations[0].id
            self.write(
                {
                    "commercial_partner_id": commercial_partner.id,
                    "partner_shipping_id": partner_shipping_id,
                    "state": "update",
                    "sale_id": default_sale_id,
                    "doc_type": parsed_order.get("doc_type"),
                }
            )
            action = self.env["ir.actions.act_window"].for_xml_id(
                "sale_order_import", "sale_order_import_action"
            )
            action["res_id"] = self.id
            return action
        else:
            return self.create_order_return_action(parsed_order, self.order_filename)

    def create_order_button(self):
        self.ensure_one()
        parsed_order = self.parse_order(
            b64decode(self.order_file), self.order_filename, self.partner_id
        )
        return self.create_order_return_action(parsed_order, self.order_filename)

    def create_order_return_action(self, parsed_order, order_filename):
        self.ensure_one()
        order = self.create_order(parsed_order, self.price_source, order_filename)
        order.message_post(
            body=_("Created automatically via file import (%s).") % self.order_filename
        )
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations")
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
                "view_id": False,
                "res_id": order.id,
            }
        )
        return action

    @api.model
    def _prepare_update_order_vals(self, parsed_order, order, partner):
        bdio = self.env["business.document.import"]
        partner = bdio._match_partner(
            parsed_order["partner"],
            parsed_order["chatter_msg"],
            partner_type="customer",
        )
        vals = {"partner_id": partner.id}
        if parsed_order.get("ship_to"):
            shipping_partner = bdio._match_shipping_partner(
                parsed_order["ship_to"], partner, parsed_order["chatter_msg"]
            )
            vals["partner_shipping_id"] = shipping_partner.id
        if parsed_order.get("order_ref"):
            vals["client_order_ref"] = parsed_order["order_ref"]
        return vals

    @api.model
    def _prepare_create_order_line(
        self, product, uom, order, import_line, price_source
    ):
        """the 'order' arg can be a recordset (in case of an update of a sale order)
        or a dict (in case of the creation of a new sale order)"""
        solo = self.env["sale.order.line"]
        vals = {
            "product_id": product.id,
            "product_uom_qty": import_line["qty"],
            "product_uom": uom.id,
        }
        if price_source == "order":
            vals["price_unit"] = import_line["price_unit"]  # TODO : fix
        elif price_source == "pricelist":
            # product_id_change is played in the inherit of create()
            # of sale.order.line cf odoo/addons/sale/models/sale.py
            # but it is not enough: we also need to play _onchange_discount()
            # to have the right discount for pricelist
            vals["order_id"] = order
            vals = solo.play_onchanges(vals, ["product_id"])
            vals.pop("order_id")
        return vals

    @api.model
    def update_order_lines(self, parsed_order, order, price_source):
        chatter = parsed_order["chatter_msg"]
        solo = self.env["sale.order.line"]
        dpo = self.env["decimal.precision"]
        bdio = self.env["business.document.import"]
        qty_prec = dpo.precision_get("Product UoS")
        price_prec = dpo.precision_get("Product Price")
        existing_lines = []
        for oline in order.order_line:
            # compute price unit without tax
            price_unit = 0.0
            if not float_is_zero(oline.product_uom_qty, precision_digits=qty_prec):
                qty = float(oline.product_uom_qty)
                price_unit = oline.price_subtotal / qty
            existing_lines.append(
                {
                    "product": oline.product_id or False,
                    "name": oline.name,
                    "qty": oline.product_uom_qty,
                    "uom": oline.product_uom,
                    "line": oline,
                    "price_unit": price_unit,
                }
            )
        compare_res = bdio.compare_lines(
            existing_lines,
            parsed_order["lines"],
            chatter,
            qty_precision=qty_prec,
            seller=False,
        )
        # NOW, we start to write/delete/create the order lines
        for oline, cdict in compare_res["to_update"].items():
            write_vals = {}
            # TODO: add support for price_source == order
            if cdict.get("qty"):
                chatter.append(
                    _(
                        "The quantity has been updated on the order line "
                        "with product '%s' from %s to %s %s"
                    )
                    % (
                        oline.product_id.display_name,
                        cdict["qty"][0],
                        cdict["qty"][1],
                        oline.product_uom.name,
                    )
                )
                write_vals["product_uom_qty"] = cdict["qty"][1]
                if price_source != "order":
                    new_price_unit = order.pricelist_id.with_context(
                        date=order.date_order, uom=oline.product_uom.id
                    ).price_get(
                        oline.product_id.id,
                        write_vals["product_uom_qty"],
                        order.partner_id.id,
                    )[
                        order.pricelist_id.id
                    ]
                    if float_compare(
                        new_price_unit, oline.price_unit, precision_digits=price_prec
                    ):
                        chatter.append(
                            _(
                                "The unit price has been updated on the order "
                                "line with product '%s' from %s to %s %s"
                            )
                            % (
                                oline.product_id.display_name,
                                oline.price_unit,
                                new_price_unit,
                                order.currency_id.name,
                            )
                        )
                        write_vals["price_unit"] = new_price_unit
            if write_vals:
                oline.write(write_vals)
        if compare_res["to_remove"]:
            to_remove_label = [
                "%s %s x %s"
                % (line.product_uom_qty, line.product_uom.name, line.product_id.name)
                for line in compare_res["to_remove"]
            ]
            chatter.append(
                _("%d order line(s) deleted: %s")
                % (len(compare_res["to_remove"]), ", ".join(to_remove_label))
            )
            compare_res["to_remove"].unlink()
        if compare_res["to_add"]:
            to_create_label = []
            for add in compare_res["to_add"]:
                line_vals = self._prepare_create_order_line(
                    add["product"], add["uom"], order, add["import_line"], price_source
                )
                line_vals["order_id"] = order.id
                new_line = solo.create(line_vals)
                to_create_label.append(
                    "%s %s x %s"
                    % (
                        new_line.product_uom_qty,
                        new_line.product_uom.name,
                        new_line.name,
                    )
                )
            chatter.append(
                _("%d new order line(s) created: %s")
                % (len(compare_res["to_add"]), ", ".join(to_create_label))
            )
        return True

    def update_order_button(self):
        self.ensure_one()
        bdio = self.env["business.document.import"]
        order = self.sale_id
        if not order:
            raise UserError(_("You must select a quotation to update."))
        parsed_order = self.parse_order(
            b64decode(self.order_file), self.order_filename, self.partner_id
        )
        currency = bdio._match_currency(
            parsed_order.get("currency"), parsed_order["chatter_msg"]
        )
        if currency != order.currency_id:
            raise UserError(
                _(
                    "The currency of the imported order (%s) is different from "
                    "the currency of the existing order (%s)"
                )
                % (currency.name, order.currency_id.name)
            )
        vals = self._prepare_update_order_vals(
            parsed_order, order, self.commercial_partner_id
        )
        if vals:
            order.write(vals)
        self.update_order_lines(parsed_order, order, self.price_source)
        bdio.post_create_or_update(parsed_order, order)
        logger.info(
            "Quotation ID %d updated via import of file %s",
            order.id,
            self.order_filename,
        )
        order.message_post(
            body=_(
                "This quotation has been updated automatically via the import of "
                "file %s"
            )
            % self.order_filename
        )
        action = self.env["ir.actions.act_window"].for_xml_id(
            "sale", "action_quotations"
        )
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
                "view_id": False,
                "res_id": order.id,
            }
        )
        return action
