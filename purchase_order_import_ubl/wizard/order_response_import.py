# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.addons.purchase_order_import.wizard.order_response_import import (
    ORDER_RESPONSE_STATUS_ACK,
    ORDER_RESPONSE_STATUS_ACCEPTED,
    ORDER_RESPONSE_STATUS_REJECTED,
    ORDER_RESPONSE_STATUS_CONDITIONAL,
    LINE_STATUS_ACCEPTED,
    LINE_STATUS_REJECTED,
    LINE_STATUS_AMEND,
)

import logging

logger = logging.getLogger(__name__)


_ORDER_RESPONSE_CODE_TO_STATUS = {
    "AB": ORDER_RESPONSE_STATUS_ACK,
    "AP": ORDER_RESPONSE_STATUS_ACCEPTED,
    "RE": ORDER_RESPONSE_STATUS_REJECTED,
    "CA": ORDER_RESPONSE_STATUS_CONDITIONAL,
}

_ORDER_LINE_STATUS_TO_STATUS = {
    "5": LINE_STATUS_ACCEPTED,
    "7": LINE_STATUS_REJECTED,
    "3": LINE_STATUS_AMEND,
}


class OrderResponseImport(models.TransientModel):
    _name = "order.response.import"
    _inherit = ["order.response.import", "base.ubl"]

    @api.model
    def parse_xml_order_document(self, xml_root):
        start_tag = "{urn:oasis:names:specification:ubl:schema:xsd:"
        if xml_root.tag == start_tag + "OrderResponse-2}OrderResponse":
            return self.parse_ubl_order_response(xml_root)
        else:
            return super(OrderResponseImport, self).parse_xml_order(xml_root)

    @api.model
    def parse_note_path(self, note_xpath):
        return "\n".join([n.text for n in note_xpath or [] if n.text])

    @api.model
    def parse_response_code(self, xml_root, ns):
        code_xpath = xml_root.xpath(
            "/main:OrderResponse/cbc:OrderResponseCode", namespaces=ns
        )
        code = code_xpath and len(code_xpath) and code_xpath[0].text
        status = _ORDER_RESPONSE_CODE_TO_STATUS.get(code)
        if not status:
            raise UserError(_("Unknown response code found '%s'") % code)
        return status

    @api.model
    def parse_line_status_code(self, line, ns):
        code_xpath = line.xpath("cbc:LineStatusCode", namespaces=ns)
        code = code_xpath and len(code_xpath) and code_xpath[0].text
        status = _ORDER_LINE_STATUS_TO_STATUS.get(code)
        if not status:
            raise UserError(
                _("Unsupported line status code found '%s'") % code
            )
        return status

    @api.model
    def parse_ubl_order_response_line(self, line, ns):
        line_item = line.xpath("cac:LineItem", namespaces=ns)[0]
        line_id_xpath = line_item.xpath("cbc:ID", namespaces=ns)
        qty_xpath = line_item.xpath("cbc:Quantity", namespaces=ns)
        qty = float(qty_xpath[0].text)
        note_xpath = line_item.xpath("cbc:Note", namespaces=ns)
        backorder_qty_xpath = line_item.xpath(
            "cbc:MaximumBackorderQuantity", namespaces=ns
        )
        backorder_qty = None
        if backorder_qty_xpath and len(backorder_qty_xpath):
            backorder_qty = float(backorder_qty_xpath[0].text)

        res_line = {
            "line_id": line_id_xpath[0].text,
            "qty": qty,
            "uom": {"unece_code": qty_xpath[0].attrib.get("unitCode")},
            "note": self.parse_note_path(note_xpath),
            "status": self.parse_line_status_code(line_item, ns),
            "backorder_qty": backorder_qty
        }
        return res_line

    # Format of parsed order response
    # {
    # 'ref': 'SO01234' # the buyer party identifier
    #                  # (specified into the Order document -> po's name)
    # 'supplier': {'vat': 'FR25499247138'},
    # 'company': {'vat': 'FR12123456789'}, # Only used to check we are not
    #                                      # importing the quote in the
    #                                      # wrong company by mistake
    # 'status': 'acknowledgement | accepted | rejected |
    #            conditionally_accepted'
    # 'currency': {'iso': 'EUR', 'symbol': u'€'},
    # 'note': 'some notes',
    # 'chatter_msg': ['msg1', 'msg2']
    # 'lines': [{
    #           'id': 123456,
    #           'qty': 2.5,
    #           'uom': {'unece_code': 'C62'},
    #           'status': 5,
    #           'note': 'my note'
    #           'backorder_qty: None  # if provided and qty != expected
    #                                 # the backorder qty will be delivered
    #                                 # in a next shipping
    #    }]
    @api.model
    def parse_ubl_order_response(self, xml_root):
        ns = xml_root.nsmap
        main_xmlns = ns.pop(None)
        ns["main"] = main_xmlns
        date_xpath = xml_root.xpath(
            "/main:OrderResponse/cbc:IssueDate", namespaces=ns
        )
        time_xpath = xml_root.xpath(
            "/main:OrderResponse/cbc:IssueTime", namespaces=ns
        )
        order_reference_xpath = xml_root.xpath(
            "/main:OrderResponse/cac:OrderReference/cbc:ID", namespaces=ns
        )

        currency_xpath = xml_root.xpath(
            "/main:OrderResponse/cbc:DocumentCurrencyCode", namespaces=ns
        )
        currency_code = False
        if currency_xpath:
            currency_code = currency_xpath[0].text
        else:
            currency_xpath = xml_root.xpath(
                "//cbc:LineExtensionAmount", namespaces=ns
            )
            if currency_xpath:
                currency_code = currency_xpath[0].attrib.get("currencyID")
        supplier_xpath = xml_root.xpath(
            "/main:OrderResponse/cac:SellerSupplierParty", namespaces=ns
        )
        supplier_dict = self.ubl_parse_supplier_party(supplier_xpath[0], ns)
        # We only take the "official references" for supplier_dict
        supplier_dict = {"vat": supplier_dict.get("vat")}
        customer_xpath_party = xml_root.xpath(
            "/main:OrderResponse/cac:BuyerCustomerParty/cac:Party",
            namespaces=ns,
        )
        company_dict_full = self.ubl_parse_party(customer_xpath_party[0], ns)
        company_dict = {}
        # We only take the "official references" for company_dict
        if company_dict_full.get("vat"):
            company_dict = {"vat": company_dict_full["vat"]}
        note_xpath = xml_root.xpath(
            "/main:OrderResponse/cbc:Note", namespaces=ns
        )
        lines_xpath = xml_root.xpath(
            "/main:OrderResponse/cac:OrderLine", namespaces=ns
        )
        res_lines = []
        for line in lines_xpath:
            res_lines.append(self.parse_ubl_order_response_line(line, ns))
        res = {
            "ref": order_reference_xpath[0].text,
            "supplier": supplier_dict,
            "company": company_dict,
            "currency": {"iso": currency_code},
            "date": len(date_xpath) and date_xpath[0].text,
            "time": len(time_xpath) and time_xpath[0].text,
            "status": self.parse_response_code(xml_root, ns),
            "note": self.parse_note_path(note_xpath),
            "lines": res_lines,
        }
        return res
