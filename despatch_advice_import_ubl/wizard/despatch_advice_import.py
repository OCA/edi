# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class DespatchAdviceImport(models.TransientModel):

    _name = "despatch.advice.import"
    _inherit = ["despatch.advice.import", "base.ubl"]

    @api.model
    def parse_xml_despatch_advice(self, xml_root):
        start_tag = "{urn:oasis:names:specification:ubl:schema:xsd:"
        if xml_root.tag == start_tag + "DespatchAdvice-2}DespatchAdvice":
            return self.parse_ubl_despatch_advice(xml_root)
        else:
            return super(DespatchAdviceImport, self).parse_xml_despatch_advice(xml_root)

    @api.model
    def parse_ubl_despatch_advice(self, xml_root):
        ns = xml_root.nsmap
        # Get main xmlns
        if None in ns:
            main_xmlns = ns.pop(None)
        else:
            main_xmlns = ns.pop("DespatchAdvice")
        ns["main"] = main_xmlns
        date_xpath = xml_root.xpath("/main:DespatchAdvice/cbc:IssueDate", namespaces=ns)
        estimated_delivery_date_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cac:Shipment/cac:Delivery/"
            "cac:EstimatedDeliveryPeriod/cbc:EndDate",
            namespaces=ns,
        )
        order_reference_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cac:OrderReference/cbc:ID", namespaces=ns
        )

        despatch_advice_type_code_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cbc:DespatchAdviceTypeCode", namespaces=ns
        )

        supplier_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cac:DespatchSupplierParty/cac:Party", namespaces=ns
        )
        # We only take the "official references" for supplier_dict
        supplier_dict = self.ubl_parse_party(supplier_xpath[0], ns)
        supplier_dict = {
            "vat": supplier_dict.get("vat"),
        }
        customer_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cac:DeliveryCustomerParty/cac:Party", namespaces=ns
        )
        customer_dict = self.ubl_parse_party(customer_xpath[0], ns)

        customer_dict = {"vat": customer_dict.get("vat")}
        lines_xpath = xml_root.xpath(
            "/main:DespatchAdvice/cac:DespatchLine", namespaces=ns
        )
        res_lines = []
        for line in lines_xpath:
            res_lines.append(self.parse_ubl_despatch_advice_line(line, ns))
        res = {
            "ref": order_reference_xpath[0].text if order_reference_xpath else "",
            "supplier": supplier_dict,
            "company": customer_dict,
            "despatch_advice_type_code": despatch_advice_type_code_xpath[0].text
            if len(despatch_advice_type_code_xpath) > 0
            else "",
            "date": len(date_xpath) and date_xpath[0].text,
            "estimated_delivery_date": len(estimated_delivery_date_xpath)
            and estimated_delivery_date_xpath[0].text,
            "lines": res_lines,
        }
        return res

    @api.model
    def parse_ubl_despatch_advice_line(self, line, ns):
        line_id_xpath = line.xpath("cbc:ID", namespaces=ns)
        qty_xpath = line.xpath("cbc:DeliveredQuantity", namespaces=ns)
        qty = float(qty_xpath[0].text)
        backorder_qty_xpath = line.xpath("cbc:OutstandingQuantity", namespaces=ns)
        backorder_qty = None
        if backorder_qty_xpath and len(backorder_qty_xpath):
            backorder_qty = float(backorder_qty_xpath[0].text)
        else:
            backorder_qty = 0

        product_ref_xpath = line.xpath(
            "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns
        )

        if len(product_ref_xpath) == 0:
            product_ref_xpath = line.xpath(
                "cac:Item/cac:BuyersItemIdentification/cbc:ID", namespaces=ns
            )

        product_lot_xpath = line.xpath(
            "cac:Item/cac:ItemInstance/cac:LotIdentification/cbc:LotNumberID",
            namespaces=ns,
        )
        order_reference_xpath = line.xpath(
            "cac:OrderLineReference/cac:OrderReference/cbc:ID", namespaces=ns
        )

        order_line_id_xpath = line.xpath(
            "cac:OrderLineReference/cbc:LineID", namespaces=ns
        )

        if not order_line_id_xpath:
            raise UserError(_("Missing line ID in the Despatch Advice."))

        res_line = {
            "line_id": line_id_xpath[0].text,
            "order_line_id": order_line_id_xpath[0].text,
            "ref": order_reference_xpath[0].text if order_reference_xpath else "",
            "qty": qty,
            "product_ref": product_ref_xpath[0].text,
            "product_lot": product_lot_xpath[0].text if product_lot_xpath else "",
            "uom": {"unece_code": qty_xpath[0].attrib.get("unitCode")},
            "backorder_qty": backorder_qty,
        }
        defaults = self.env.context.get("despatch_advice_import__default_vals", {}).get(
            "lines", {}
        )
        res_line.update(defaults)
        return res_line

    @api.model
    def ubl_parse_party(self, party_node, ns):
        partner_name_xpath = party_node.xpath("cac:PartyName/cbc:Name", namespaces=ns)
        if not partner_name_xpath:
            partner_name_xpath = party_node.xpath(
                "cac:PartyLegalEntity/cbc:RegistrationName", namespaces=ns
            )

        vat_xpath = party_node.xpath("cac:PartyIdentification/cbc:ID", namespaces=ns)
        partner_dict = {
            "vat": vat_xpath[0].text
            if vat_xpath and vat_xpath[0].attrib.get("schemeName").upper()
            else False,
            "name": partner_name_xpath[0].text,
        }
        address_xpath = party_node.xpath("cac:PostalAddress", namespaces=ns)
        if address_xpath:
            address_dict = self.ubl_parse_address(address_xpath[0], ns)
            partner_dict.update(address_dict)
        return partner_dict
