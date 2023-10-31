# Copyright 2016-2017 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from base64 import b64decode, b64encode

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import AND
from odoo.tools import config, float_compare, float_is_zero

logger = logging.getLogger(__name__)


class SaleOrderImport(models.TransientModel):
    _name = "sale.order.import"
    _description = "Sale Order Import from Files"

    state = fields.Selection(
        [("import", "Import"), ("update", "Update")], default="import"
    )
    partner_id = fields.Many2one("res.partner", string="Customer")
    import_type = fields.Selection(
        [("xml", "XML"), ("pdf", "PDF")],
        required=True,
        default=None,
        help="Select a type which you want to import",
    )
    order_file = fields.Binary(
        string="Request for Quotation or Order",
        required=True,
        help="Upload a Request for Quotation or an Order file. Supported "
        "formats: XML and PDF (PDF with an embeded XML file).",
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
    # Confirm order after creating Sale Order
    confirm_order = fields.Boolean(default=False)

    @api.onchange("order_file")
    def order_file_change(self):
        if not self.order_filename or not self.order_file:
            self.doc_type = False
            return

        doc_type = self._parse_file(
            self.order_filename, b64decode(self.order_file), detect_doc_type=True
        )
        if doc_type is None:
            return {"warning": self._unsupported_file_msg(self.order_filename)}
        self.doc_type = doc_type

    def _get_supported_types(self):
        # Define the supported types dictionary
        supported_types = {
            "xml": ("application/xml", "text/xml"),
            "pdf": ("application/pdf"),
        }
        return supported_types

    def _parse_file(self, filename, filecontent, detect_doc_type=False):
        assert filename, "Missing filename"
        assert filecontent, "Missing file content"
        filetype = mimetypes.guess_type(filename)
        logger.debug("Order file mimetype: %s", filetype)
        mimetype = filetype[0]
        supported_types = self._get_supported_types()
        # Check if the selected import type is supported
        if self.import_type not in supported_types:
            raise UserError(_("Please select a valid import type before importing!"))

        # Check if the detected MIME type is supported for the selected import type
        if mimetype not in supported_types[self.import_type]:
            raise UserError(
                _(
                    "This file '%(filename)s' is not recognized as a %(type)s file. "
                    "Please check the file and its extension.",
                    filename=filename,
                    type=self.import_type.upper(),
                )
            )
        if hasattr(self, "parse_%s_order" % self.import_type):
            return getattr(self, "parse_%s_order" % self.import_type)(
                filecontent, detect_doc_type=detect_doc_type
            )
        else:
            raise UserError(
                _(
                    "This Import Type is not supported. Did you install "
                    "the module to support this type?"
                )
            )

    def _unsupported_file_msg(self, filename):
        return {
            "title": _("Unsupported file format"),
            "message": _(
                "This file '%s' is not recognised as a XML nor "
                "PDF file. Please check the file and it's "
                "extension."
            )
            % filename,
        }

    @api.model
    def _parse_xml(self, data):
        if not data:
            return None, _("No data provided")
        xml_root = None
        try:
            xml_root = etree.fromstring(data)
            error_msg = None
        except etree.XMLSyntaxError:
            error_msg = _("This XML file is not XML-compliant")
            return xml_root, error_msg
        return xml_root, error_msg

    @api.model
    def parse_xml_order(self, data, detect_doc_type=False):
        if not self.env.context.get("xml_root", False):
            xml_root, error_msg = self._parse_xml(data)
        else:
            xml_root = data
            error_msg = None
        if (xml_root is None or not len(xml_root)) and error_msg:
            raise UserError(error_msg)
        raise NotImplementedError(
            _(
                "This type of XML RFQ/order is not supported. Did you install "
                "the module to support this XML format?"
            )
        )

    @api.model
    def parse_pdf_order(self, order_file, detect_doc_type=False):
        """
        Get PDF attachments, filter on XML files and call import_order_xml
        """
        xml_files_dict = self.env["pdf.helper"].pdf_get_xml_files(order_file)
        if not xml_files_dict:
            raise UserError(_("There are no embedded XML file in this PDF file."))
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_order = self.with_context(xml_root=True).parse_xml_order(
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
    def _search_existing_order_domain(
        self, parsed_order, commercial_partner, state_domain
    ):
        return AND(
            [
                state_domain,
                [
                    ("client_order_ref", "=", parsed_order["order_ref"]),
                    ("commercial_partner_id", "=", commercial_partner.id),
                ],
            ]
        )

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
        # FIXME: this should work but it's not as it breaks core price compute
        # so_vals = soo.default_get(soo._fields.keys())
        so_vals = {
            "partner_id": partner.id,
            "client_order_ref": parsed_order.get("order_ref"),
        }
        self._validate_currency(partner, currency)
        self._validate_existing_orders(partner, parsed_order)
        so_vals = soo.play_onchanges(so_vals, ["partner_id"])
        so_vals["order_line"] = []
        if parsed_order.get("ship_to"):
            shipping_partner = bdio._match_shipping_partner(
                parsed_order["ship_to"], partner, parsed_order["chatter_msg"]
            )
            so_vals["partner_shipping_id"] = shipping_partner.id

        if parsed_order.get("delivery_detail"):
            so_vals.update(parsed_order.get("delivery_detail"))

        if parsed_order.get("invoice_to"):
            invoicing_partner = bdio._match_partner(
                parsed_order["invoice_to"], parsed_order["chatter_msg"], partner_type=""
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

        defaults = self.env.context.get("sale_order_import__default_vals", {}).get(
            "order", {}
        )
        so_vals.update(defaults)
        return so_vals

    def _validate_currency(self, partner, currency):
        if partner.property_product_pricelist.currency_id != currency:
            raise UserError(
                _(
                    "The customer '%(name)s' has a pricelist '%(pricelist)s' but the "
                    "currency of this order is '%(currency)s'.",
                    name=partner.display_name,
                    pricelist=partner.property_product_pricelist.display_name,
                    currency=currency.name,
                )
            )

    def _validate_existing_orders(self, partner, parsed_order):
        if not parsed_order.get("order_ref"):
            return
        commercial_partner = partner.commercial_partner_id
        existing_orders = self.env["sale.order"].search(
            self._search_existing_order_domain(
                parsed_order, commercial_partner, [("state", "!=", "cancel")]
            ),
            limit=1,
        )
        if existing_orders:
            raise UserError(
                _(
                    "An order of customer '%(partner)s' with reference '%(ref)s' "
                    "already exists: %(name)s (state: %(state)s)",
                    partner=partner.display_name,
                    ref=parsed_order["order_ref"],
                    name=existing_orders[0].name,
                    state=existing_orders[0].state,
                )
            )

    @api.model
    def create_order(self, parsed_order, price_source, order_filename=None):
        soo = self.env["sale.order"].with_context(mail_create_nosubscribe=True)
        bdio = self.env["business.document.import"]
        so_vals = self._prepare_order(parsed_order, price_source)
        order = soo.create(so_vals)
        bdio.post_create_or_update(parsed_order, order, doc_filename=order_filename)
        logger.info("Sale Order ID %d created", order.id)
        if self.confirm_order:
            order.action_confirm()
            logger.info("Sale Order ID %d confirmed", order.id)
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
        parsed_order = self._parse_file(order_filename, order_file)
        logger.debug("Result of order parsing: %s", parsed_order)
        defaults = (
            ("attachments", {}),
            ("chatter_msg", []),
        )
        for key, val in defaults:
            parsed_order.setdefault(key, val)

        parsed_order["attachments"][order_filename] = b64encode(order_file)
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
            self._search_existing_order_domain(
                parsed_order, commercial_partner, [("state", "in", ("draft", "sent"))]
            )
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
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "sale_order_import.sale_order_import_action"
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

    # TODO: add tests
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
        vals = {}
        # Ensure the company is loaded before we play onchanges.
        # Yes, `company_id` is related to `order_id.company_id`
        # but when we call `play_onchanges` it will be empty
        # w/out this precaution.
        company_id = self._prepare_order_line_get_company_id(order)
        vals.update(
            {
                "product_id": product.id,
                "product_uom_qty": import_line["qty"],
                "product_uom": uom.id,
                "company_id": company_id,
            }
        )

        if price_source == "order":
            if "price_unit" not in import_line:
                raise UserError(
                    _(
                        "No price is defined in the file. Please double check "
                        "file or select Pricelist as the source for prices."
                    )
                )
            vals["price_unit"] = import_line["price_unit"]
        elif price_source == "pricelist":
            # product_id_change is played in the inherit of create()
            # of sale.order.line cf odoo/addons/sale/models/sale.py
            # but it is not enough: we also need to play _onchange_discount()
            # to have the right discount for pricelist
            vals["order_id"] = order
            vals.pop("order_id")

        # Handle additional fields dynamically if available.
        # This way, if you add a field to a record and it's value is injected by a parser
        # you won't have to override `_prepare_create_order_line` to let it propagate.
        for k, v in import_line.items():
            if k not in vals and k in solo._fields:
                vals[k] = v

        defaults = self.env.context.get("sale_order_import__default_vals", {}).get(
            "lines", {}
        )
        vals.update(defaults)
        return vals

    def _prepare_order_line_get_company_id(self, order):
        company_id = self.env.company.id
        if isinstance(order, models.Model):
            company_id = order.company_id.id
        elif isinstance(order, dict):
            company_id = order.get("company_id") or company_id
        return company_id

    # TODO: add tests
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
                        "with product '%(product)s' from %(qty0)s to %(qty1)s %(uom)s",
                        product=oline.product_id.display_name,
                        qty0=cdict["qty"][0],
                        qty1=cdict["qty"][1],
                        uom=oline.product_uom.name,
                    )
                )
                write_vals["product_uom_qty"] = cdict["qty"][1]
                if price_source != "order":
                    new_price_unit = order.pricelist_id.with_context(
                        date=order.date_order, uom=oline.product_uom.id
                    )._price_get(oline.product_id, write_vals["product_uom_qty"],)[
                        order.pricelist_id.id
                    ]
                    if float_compare(
                        new_price_unit, oline.price_unit, precision_digits=price_prec
                    ):
                        chatter.append(
                            _(
                                "The unit price has been updated on the order "
                                "line with product '%(product)s' from %(old)s to "
                                "%(new)s %(currency)s",
                                product=oline.product_id.display_name,
                                old=oline.price_unit,
                                new=new_price_unit,
                                currency=order.currency_id.name,
                            )
                        )
                        write_vals["price_unit"] = new_price_unit
                write_vals.update(self._prepare_update_order_line_vals(cdict))
            if write_vals:
                oline.write(write_vals)
        if compare_res["to_remove"]:
            to_remove_label = [
                "%s %s x %s"
                % (line.product_uom_qty, line.product_uom.name, line.product_id.name)
                for line in compare_res["to_remove"]
            ]
            chatter.append(
                _(
                    "%(orders)s order line(s) deleted: %(label)s",
                    orders=len(compare_res["to_remove"]),
                    label=", ".join(to_remove_label),
                )
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
                _(
                    "%(orders)s new order line(s) created: %(label)s",
                    orders=len(compare_res["to_add"]),
                    label=", ".join(to_create_label),
                )
            )
        return True

    def _prepare_update_order_line_vals(self, change_dict):
        # Allows other module to update some fields on the line
        return {}

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
                    "The currency of the imported order (%(old)s) is different from "
                    "the currency of the existing order (%(new)s)",
                    old=currency.name,
                    new=order.currency_id.name,
                )
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
        action = self.env["ir.actions.act_window"]._for_xml_id("sale.action_quotations")
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
                "view_id": False,
                "res_id": order.id,
            }
        )
        return action
