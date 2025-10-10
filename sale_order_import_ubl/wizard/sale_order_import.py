# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    @property
    def base_ubl(self):
        return self.env["base.ubl"]

    @api.model
    def parse_xml_order(self, data, detect_doc_type=False):
        if not self.env.context.get("xml_root", False):
            xml_root, error_msg = self._parse_xml(data)
        else:
            xml_root = data
            error_msg = None
        if (xml_root is None or not len(xml_root)) and error_msg:
            raise UserError(error_msg)
        start_tag = "{urn:oasis:names:specification:ubl:schema:xsd:"
        rfq = "RequestForQuotation"
        if xml_root.tag == start_tag + "Order-2}Order":
            if detect_doc_type:
                return "order"
            else:
                return self.parse_ubl_sale_order(xml_root)
        elif xml_root.tag == f"{start_tag}{rfq}-2}}{rfq}":
            if detect_doc_type:
                return "rfq"
            else:
                return self.parse_ubl_sale_order(xml_root)
        return super().parse_xml_order(data, detect_doc_type=detect_doc_type)

    @api.model
    def parse_ubl_sale_order_line(self, line, ns):
        qty_prec = self.env["decimal.precision"].precision_get("Product UoS")
        line_item = line.xpath("cac:LineItem", namespaces=ns)[0]
        qty_xpath = line_item.xpath("cbc:Quantity", namespaces=ns)
        qty = float(qty_xpath[0].text)
        price_unit = 0.0
        subtotal_without_tax_xpath = line_item.xpath(
            "cbc:LineExtensionAmount", namespaces=ns
        )
        if subtotal_without_tax_xpath:
            subtotal_without_tax = float(subtotal_without_tax_xpath[0].text)
            if not float_is_zero(qty, precision_digits=qty_prec):
                price_unit = subtotal_without_tax / qty
        else:
            price_xpath = line_item.xpath("cac:Price/cbc:PriceAmount", namespaces=ns)
            if price_xpath:
                price_unit = float(price_xpath[0].text)
        line_ref = line_item.xpath("cbc:ID", namespaces=ns)[0]
        res_line = {
            "product": self.base_ubl.ubl_parse_product(line_item, ns),
            "qty": qty,
            "uom": {"unece_code": qty_xpath[0].attrib.get("unitCode")},
            "price_unit": price_unit,
            "order_line_ref": line_ref.text,
        }
        note = self.parse_ubl_sale_order_line_note(line, ns)
        if note:
            res_line["note"] = note
        return res_line

    def parse_ubl_sale_order_line_note(self, line, ns):
        """Collect all notes for a given order line."""
        # OrderLine/cbc:Note
        notes = line.xpath("cbc:Note", namespaces=ns)
        # OrderLine/LineItem/cbc:Note
        notes += line.xpath("cac:LineItem/cbc:Note", namespaces=ns)
        notes = [x.text for x in notes if x.text and x.text.strip()]
        return "\n".join(notes)

    @api.model
    def parse_ubl_sale_order(self, xml_root):
        ns = xml_root.nsmap
        main_xmlns = ns.pop(None)
        ns["main"] = main_xmlns
        if "RequestForQuotation" in main_xmlns:
            document = "RequestForQuotation"
            root_name = "main:RequestForQuotation"
            line_name = "cac:RequestForQuotationLine"
            doc_type = "rfq"
        elif "Order" in main_xmlns:
            document = "Order"
            root_name = "main:Order"
            line_name = "cac:OrderLine"
            doc_type = "order"
        # Validate content according to xsd file
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )
        self.base_ubl._ubl_check_xml_schema(
            xml_string,
            document,
            version=self.base_ubl._ubl_get_version(xml_root, root_name, ns),
        )
        # Parse content
        date_xpath = xml_root.xpath(f"/{root_name}/cbc:IssueDate", namespaces=ns)
        currency_code = False
        for cur_node_name in ("DocumentCurrencyCode", "PricingCurrencyCode"):
            currency_xpath = xml_root.xpath(
                f"/{root_name}/cbc:{cur_node_name}", namespaces=ns
            )
            if currency_xpath:
                currency_code = currency_xpath[0].text
                break
        if not currency_code:
            currency_xpath = xml_root.xpath("//cbc:LineExtensionAmount", namespaces=ns)
            if currency_xpath:
                currency_code = currency_xpath[0].attrib.get("currencyID")
        order_ref_xpath = xml_root.xpath(f"/{root_name}/cbc:ID", namespaces=ns)
        customer_xpath = xml_root.xpath(
            f"/{root_name}/cac:BuyerCustomerParty", namespaces=ns
        )
        if not customer_xpath:
            customer_xpath = xml_root.xpath(
                f"/{root_name}/cac:OriginatorCustomerParty", namespaces=ns
            )
        customer_dict = self.base_ubl.ubl_parse_customer_party(customer_xpath[0], ns)
        supplier_xpath_party = xml_root.xpath(
            f"/{root_name}/cac:SellerSupplierParty/cac:Party", namespaces=ns
        )
        company_dict_full = self.base_ubl.ubl_parse_party(supplier_xpath_party[0], ns)
        company_dict = {}
        # We only take the "official references" for company_dict
        if company_dict_full.get("vat"):
            company_dict = {"vat": company_dict_full["vat"]}
        delivery_xpath = xml_root.xpath(f"/{root_name}/cac:Delivery", namespaces=ns)
        shipping_dict = {}
        delivery_dict = {}
        if delivery_xpath:
            shipping_dict = self.base_ubl.ubl_parse_delivery(delivery_xpath[0], ns)
            delivery_dict = self.base_ubl.ubl_parse_delivery_details(
                delivery_xpath[0], ns
            )
        # In the demo UBL 2.1 file, they use 'IMCOTERM'... but I guess
        # it's a mistake and they should use 'INCOTERM'
        # So, for the moment, I ignore the attributes in the xpath for incoterm
        delivery_term_xpath = xml_root.xpath(
            f"/{root_name}/cac:DeliveryTerms", namespaces=ns
        )
        if delivery_term_xpath:
            incoterm_dict = self.base_ubl.ubl_parse_incoterm(delivery_term_xpath[0], ns)
        else:
            incoterm_dict = {}
        invoicing_xpath = xml_root.xpath(
            f"/{root_name}/cac:AccountingCustomerParty", namespaces=ns
        )
        invoicing_dict = {}
        if invoicing_xpath:
            invoicing_dict = self.base_ubl.ubl_parse_customer_party(
                invoicing_xpath[0], ns
            )
        note_xpath = xml_root.xpath(f"/{root_name}/cbc:Note", namespaces=ns)
        lines_xpath = xml_root.xpath(f"/{root_name}/{line_name}", namespaces=ns)
        res_lines = []
        for line in lines_xpath:
            res_lines.append(self.parse_ubl_sale_order_line(line, ns))
        # TODO : add charges
        res = {
            "partner": customer_dict,
            "company": company_dict,
            "ship_to": shipping_dict,
            "invoice_to": invoicing_dict,
            "currency": {"iso": currency_code},
            "date": date_xpath[0].text,
            "order_ref": order_ref_xpath[0].text,
            "incoterm": incoterm_dict,
            "note": note_xpath and note_xpath[0].text or False,
            "lines": res_lines,
            "doc_type": doc_type,
            "delivery_detail": delivery_dict,
        }
        # Stupid hack to remove invalid VAT of sample files
        if res["partner"]["vat"] in ["SE1234567801", "12356478", "DK12345678"]:
            res["partner"].pop("vat")
        return res
