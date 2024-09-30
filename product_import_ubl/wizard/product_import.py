# Copyright 2022 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models
from odoo.tools import str2bool

CATALOGUE_NS = "urn:oasis:names:specification:ubl:schema:xsd:Catalogue-2"
CATALOGUE_TAG = "{%s}Catalogue" % CATALOGUE_NS


class XPathGetter(object):
    _missing = etree.Element("Missing")

    def __init__(self, element, namespaces):
        self._xpath = element.xpath
        self._ns = namespaces

    def xpath(self, path):
        # Return a list of elements
        items = self._xpath(path, namespaces=self._ns)
        return items

    def xpath_get(self, path):
        # Return 1 element
        items = self._xpath(path, namespaces=self._ns)
        return items[0] if items else self._missing

    def xpath_text(self, path, default=False):
        # Return text or False
        items = self._xpath(path, namespaces=self._ns)
        return items[0].text if items else default

    get = xpath_get
    text = xpath_text


class ProductImport(models.TransientModel):
    _inherit = "product.import"

    @api.model
    def parse_xml_catalogue(self, xml_root, detect_doc_type=False):
        if xml_root.tag == CATALOGUE_TAG:
            if detect_doc_type:
                return "catalogue"
            return self.parse_ubl_catalogue(xml_root)
        return super().parse_xml_catalogue(xml_root, detect_doc_type=detect_doc_type)

    @api.model
    def parse_ubl_catalogue_line(self, line, ns):
        ubl = self.env["base.ubl"]
        xline = XPathGetter(line, ns)

        # Get product basic info:
        #  - code: cac:Item/cac:SellersItemIdentification/cbc:ID
        #  - barcode: cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID='GTIN']
        product_vals = ubl.ubl_parse_product(line, ns)

        # Fill available data
        ele_price = xline.get(
            "cac:RequiredItemLocationQuantity/cac:Price/cbc:PriceAmount"
        )
        currency = ele_price.attrib.get("currencyID") or False
        min_qty = float(
            xline.text("cac:RequiredItemLocationQuantity/cbc:MinimumQuantity")
            or xline.text("cbc:MinimumOrderQuantity")
        )
        # Get product weight
        ele_weight = xline.get(
            "cac:Item/cac:Dimension[cbc:AttributeID='Weight']/cbc:Measure"
        )
        weight_unit = ele_weight.attrib.get("unitCode") or False

        product_vals.update(
            {
                "active": str2bool(
                    xline.text("cbc:OrderableIndicator", default="true")
                ),
                "name": xline.text("cac:Item/cbc:Name"),
                "description": xline.text("cac:Item/cbc:Description"),
                "external_ref": xline.text("cbc:ID"),
                "uom": {"unece_code": xline.text("cbc:OrderableUnit")},
                "product_code": xline.text(
                    "cac:Item/cac:ManufacturersItemIdentification/cbc:ID"
                ),
                "weight": float(ele_weight.text or 0),
                "weight_uom": {"unece_code": weight_unit} if weight_unit else False,
                # Seller info
                "price": float(ele_price.text or 0),
                "currency": {"iso": currency} if currency else False,
                "min_qty": min_qty,
                "sale_delay": xline.text(
                    "cac:RequiredItemLocationQuantity/cbc:LeadTimeMeasure"
                ),
            }
        )
        return product_vals

    @api.model
    def parse_ubl_catalogue(self, xml_root):
        ubl = self.env["base.ubl"]
        ns = xml_root.nsmap
        # Empty namespace prefix is not supported in XPath
        ns["main"] = ns.pop(None)
        assert ns["main"] == CATALOGUE_NS
        doc_type = "catalogue"
        document = "Catalogue"
        root_name = f"main:{document}"
        line_name = f"cac:{document}Line"

        # Validate content according to xsd file
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )
        ubl._ubl_check_xml_schema(
            xml_string, document, version=ubl._ubl_get_version(xml_root, root_name, ns)
        )
        # Parse content
        xroot = XPathGetter(xml_root, ns)
        company_xpath = xroot.get(f"/{root_name}/cac:ReceiverParty")
        company_dict = ubl.ubl_parse_party(company_xpath, ns)
        supplier_xpath = xroot.get(f"/{root_name}/cac:SellerSupplierParty")
        supplier_dict = ubl.ubl_parse_supplier_party(supplier_xpath, ns)

        res_lines = [
            self.parse_ubl_catalogue_line(line, ns)
            for line in xroot.xpath(f"/{root_name}/{line_name}")
        ]
        res = {
            "doc_type": doc_type,
            "date": xroot.text(f"/{root_name}/cbc:IssueDate"),
            "ref": xroot.text(f"/{root_name}/cbc:ID"),
            "company": company_dict,
            "seller": supplier_dict,
            "products": res_lines,
        }
        return res
