# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# Copyright 2020 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class BaseUbl(models.AbstractModel):
    _inherit = "base.ubl"

    # ==================== METHODS TO PARSE UBL files

    @api.model
    def _ubl_get_version(self, xml_root, root_name, ns):
        version_xpath = xml_root.xpath(f"/{root_name}/cbc:UBLVersionID", namespaces=ns)
        if not version_xpath:
            raise UserError(
                _(
                    "The UBL XML file does not contain the version "
                    "for validating the content according to the schema."
                )
            )
        return version_xpath[0].text.strip()

    @api.model
    def ubl_parse_customer_party(self, party_node, ns):
        ref_xpath = party_node.xpath("cbc:SupplierAssignedAccountID", namespaces=ns)
        party_node = party_node.xpath("cac:Party", namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict["ref"] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_supplier_party(self, party_node, ns):
        ref_xpath = party_node.xpath("cbc:CustomerAssignedAccountID", namespaces=ns)
        party_node = party_node.xpath("cac:Party", namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict["ref"] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_party(self, party_node, ns):
        partner_name_xpath = party_node.xpath("cac:PartyName/cbc:Name", namespaces=ns)
        vat_xpath = party_node.xpath("cac:PartyTaxScheme/cbc:CompanyID", namespaces=ns)
        website_xpath = party_node.xpath("cbc:WebsiteURI", namespaces=ns)
        contact_name_xpath = party_node.xpath("cac:Contact/cbc:Name", namespaces=ns)
        contact_email_xpath = party_node.xpath(
            "cac:Contact/cbc:ElectronicMail", namespaces=ns
        )
        contact_phone_xpath = party_node.xpath(
            "cac:Contact/cbc:Telephone", namespaces=ns
        )
        partner_dict = {
            "vat": vat_xpath and vat_xpath[0].text or False,
            "name": partner_name_xpath and partner_name_xpath[0].text or False,
            "website": website_xpath and website_xpath[0].text or False,
            "contact": contact_name_xpath and contact_name_xpath[0].text or False,
            "email": contact_email_xpath and contact_email_xpath[0].text or False,
            "phone": contact_phone_xpath and contact_phone_xpath[0].text or False,
        }
        id_nodes = party_node.xpath("cac:PartyIdentification/cbc:ID", namespaces=ns)
        id_numbers = []
        for id_node in id_nodes:
            id_numbers.append(
                {"value": id_node.text, "schemeID": id_node.attrib.get("schemeID")}
            )
        partner_dict["id_number"] = id_numbers
        address_xpath = party_node.xpath("cac:PostalAddress", namespaces=ns)
        if address_xpath:
            address_dict = self.ubl_parse_address(address_xpath[0], ns)
            partner_dict.update(address_dict)
        return partner_dict

    @api.model
    def ubl_parse_address(self, address_node, ns):
        country_code_xpath = address_node.xpath(
            "cac:Country/cbc:IdentificationCode", namespaces=ns
        )
        country_code = country_code_xpath and country_code_xpath[0].text or False
        state_code_xpath = address_node.xpath("cbc:CountrySubentityCode", namespaces=ns)
        state_code = state_code_xpath and state_code_xpath[0].text or False
        street_xpath = address_node.xpath("cbc:StreetName", namespaces=ns)
        street2_xpath = address_node.xpath("cbc:AdditionalStreetName", namespaces=ns)
        street_number_xpath = address_node.xpath("cbc:BuildingNumber", namespaces=ns)
        city_xpath = address_node.xpath("cbc:CityName", namespaces=ns)
        zip_xpath = address_node.xpath("cbc:PostalZone", namespaces=ns)
        zip_code = (
            zip_xpath
            and zip_xpath[0].text
            and zip_xpath[0].text.replace(" ", "")
            or False
        )
        address_dict = {
            "street": street_xpath and street_xpath[0].text or False,
            "street_number": street_number_xpath
            and street_number_xpath[0].text
            or False,
            "street2": street2_xpath and street2_xpath[0].text or False,
            "city": city_xpath and city_xpath[0].text or False,
            "zip": zip_code,
            "state_code": state_code,
            "country_code": country_code,
        }
        return address_dict

    @api.model
    def ubl_parse_delivery(self, delivery_node, ns):
        party_xpath = delivery_node.xpath("cac:DeliveryParty", namespaces=ns)
        if party_xpath:
            partner_dict = self.ubl_parse_party(party_xpath[0], ns)
        else:
            partner_dict = {}
        postal_xpath = delivery_node.xpath(
            "cac:DeliveryParty/cac:PostalAddress", namespaces=ns
        )
        if not postal_xpath:
            delivery_address_xpath = delivery_node.xpath(
                "cac:DeliveryLocation/cac:Address", namespaces=ns
            )
            if not delivery_address_xpath:
                delivery_address_xpath = delivery_node.xpath(
                    "cac:DeliveryAddress", namespaces=ns
                )
            if delivery_address_xpath:
                partner_dict.update(
                    self.ubl_parse_address(delivery_address_xpath[0], ns)
                )
        return partner_dict

    @api.model
    def ubl_parse_delivery_details(self, delivery_node, ns):
        delivery_dict = {}
        latest_date = delivery_node.xpath("cbc:LatestDeliveryDate", namespaces=ns)
        latest_time = delivery_node.xpath("cbc:LatestDeliveryTime", namespaces=ns)
        if latest_date:
            latest_delivery = latest_date[0].text
            if latest_time:
                latest_delivery += " " + latest_time[0].text[:-3]
            delivery_dict["commitment_date"] = latest_delivery
        return delivery_dict

    def ubl_parse_incoterm(self, delivery_term_node, ns):
        incoterm_xpath = delivery_term_node.xpath("cbc:ID", namespaces=ns)
        if incoterm_xpath:
            incoterm_dict = {"code": incoterm_xpath[0].text}
            return incoterm_dict
        return {}

    def ubl_parse_product(self, line_node, ns):
        barcode_xpath = line_node.xpath(
            "cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID='GTIN']",
            namespaces=ns,
        )
        code_xpath = line_node.xpath(
            "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns
        )
        product_dict = {
            "barcode": barcode_xpath and barcode_xpath[0].text or False,
            "code": code_xpath and code_xpath[0].text or False,
        }
        return product_dict
