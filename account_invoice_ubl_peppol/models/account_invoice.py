# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models
from odoo.osv import expression


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def get_payment_identifier(self):
        return self.reference

    def _account_invoice_ubl_use_peppol(self):
        """Returns True when we should use PEPPOL"""
        domain = self.company_id.get_ubl_domain_peppol()
        if not domain:
            return True
        return bool(
            self.search(expression.AND([[("id", "in", self.ids)], domain]), limit=1)
        )

    def generate_ubl_xml_string(self, version="2.1"):
        self.ensure_one()
        if self._account_invoice_ubl_use_peppol():
            this = self.with_context(account_invoice_ubl_use_peppol=True)
        else:
            this = self
        return super(AccountInvoice, this).generate_ubl_xml_string(version=version)

    def _ubl_add_header(self, parent_node, ns, version="2.1"):
        res = super()._ubl_add_header(parent_node, ns, version=version)
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # PEPPOL 3.0 BIS CustomizationID
        customization_id = etree.Element(ns["cbc"] + "CustomizationID")
        customization_id.text = (
            "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
        )

        # PEPPOL-EN16931-R001, PEPPOL-EN16931-R007: Business process
        profile_id = etree.Element(ns["cbc"] + "ProfileID")
        profile_id.text = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

        # Add items right after UBLVersionID
        ubl_version_id = parent_node.find(ns["cbc"] + "UBLVersionID")
        ubl_version_id.addnext(profile_id)
        ubl_version_id.addnext(customization_id)
        return res

    @api.multi
    def _ubl_add_order_reference(self, parent_node, ns, version="2.1"):
        res = super()._ubl_add_order_reference(parent_node, ns, version=version)
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # use the invoice number as default value for cac:OrderReference as in odoo 17.0
        order_ref_node_name = ns["cac"] + "OrderReference"
        order_ref_id_node_name = ns["cbc"] + "ID"
        order_ref = parent_node.find(order_ref_node_name)
        if order_ref is None:
            order_ref = etree.SubElement(parent_node, order_ref_node_name)
        order_ref_id = order_ref.find(order_ref_id_node_name)
        if order_ref_id is None:
            order_ref_id = etree.SubElement(order_ref, order_ref_id_node_name)
            order_ref_id.text = self.number
        return res

    @api.model
    def _ubl_add_payment_means(
        self,
        partner_bank,
        payment_mode,
        date_due,
        parent_node,
        ns,
        payment_identifier=None,
        version="2.1",
    ):
        res = super()._ubl_add_payment_means(
            partner_bank,
            payment_mode,
            date_due,
            parent_node,
            ns,
            version=version,
            payment_identifier=payment_identifier,
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-CR-412: A UBL invoice should not include the PaymentMeans PaymentDueDate
        invoice = parent_node
        payment_means = invoice.find(ns["cac"] + "PaymentMeans")
        if payment_means is not None:
            payment_due_date = payment_means.find(ns["cbc"] + "PaymentDueDate")
            if payment_due_date is not None:
                payment_means.remove(payment_due_date)

            # UBL-CR-413: A UBL invoice should not include the PaymentMeans
            #             PaymentChannelCode
            channel_code = payment_means.find(ns["cbc"] + "PaymentChannelCode")
            if channel_code is not None:
                payment_means.remove(channel_code)

            # UBL-CR-664: A UBL invoice should not include the
            #             FinancialInstitutionBranch FinancialInstitution
            payee_fin_account = payment_means.find(ns["cac"] + "PayeeFinancialAccount")
            if payee_fin_account is not None:
                payee_fin_account_id = payee_fin_account.find(ns["cbc"] + "ID")
                if payee_fin_account_id is not None:
                    payee_fin_account_id.attrib.pop("schemeName", None)
                institution_branch = payee_fin_account.find(
                    ns["cac"] + "FinancialInstitutionBranch"
                )
                if institution_branch is not None:
                    institution = institution_branch.find(
                        ns["cac"] + "FinancialInstitution"
                    )
                    if institution is not None:
                        institution_branch_id = institution_branch.find(
                            ns["cbc"] + "ID"
                        )
                        if institution_branch_id is None:
                            # get the bic from FinancialInstitution ID
                            bic = institution.find(ns["cbc"] + "ID")
                            if bic is not None:
                                institution_branch_id = etree.SubElement(
                                    institution_branch,
                                    ns["cbc"] + "ID",
                                )
                                institution_branch_id.text = bic.text
                        institution_branch.remove(institution)

            # UBL-CR-661: A UBL invoice should not include the PaymentMeansCode listID
            payment_means_code = payment_means.find(ns["cbc"] + "PaymentMeansCode")
            if payment_means_code is not None:
                payment_means_code.attrib.pop("listID", None)
        return res

    def _ubl_add_invoice_line_tax_total(self, iline, parent_node, ns, version="2.1"):
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return super()._ubl_add_invoice_line_tax_total(
                iline, parent_node, ns, version=version
            )

        # UBL-CR-561: A UBL invoice should not include the InvoiceLine TaxTotal
        return None

    def _ubl_add_party(
        self, partner, company, node_name, parent_node, ns, version="2.1"
    ):
        res = super()._ubl_add_party(
            partner, company, node_name, parent_node, ns, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res
        party = parent_node.find(ns["cac"] + node_name)

        # PEPPOL-EN16931-R020: EndpointID
        endpoint_dict = partner._get_peppol_endpoint_id()
        endpoint_id = endpoint_dict.get("endpoint_id")
        scheme_id = endpoint_dict.get("scheme_id")
        if scheme_id and endpoint_id:
            endpoint_id_element = etree.SubElement(
                parent_node, ns["cbc"] + "EndpointID", schemeID=scheme_id
            )
            endpoint_id_element.text = endpoint_id
            party_name = party.find(ns["cac"] + "PartyName")
            party_name.addprevious(endpoint_id_element)

        # UBL-CR-143: A UBL invoice should not include the
        #             AccountingSupplierParty Party WebsiteURI
        # UBL-CR-206: A UBL invoice should not include the
        #             AccountingCustomerParty Party WebsiteURI
        website_uri = party.find(ns["cbc"] + "WebsiteURI")
        if website_uri is not None:
            party.remove(website_uri)

        # UBL-CR-166: A UBL invoice should not include the AccountingSupplierParty
        #             Party PostalAddress Country Name
        # UBL-CR-229: A UBL invoice should not include the AccountingCustomerParty
        #             Party PostalAddress Country Name
        postal_address = party.find(ns["cac"] + "PostalAddress")
        if postal_address is not None:
            country = postal_address.find(ns["cac"] + "Country")
            if country is not None:
                country_name = country.find(ns["cbc"] + "Name")
                if country_name is not None:
                    country.remove(country_name)

        # UBL-CR-209: A UBL invoice should not include the AccountingCustomerParty
        #             Party Language
        # UBL-CR-146: A UBL invoice should not include the AccountingSupplierParty
        #             Party Language
        if party is not None:
            language = party.find(ns["cac"] + "Language")
            if language is not None:
                party.remove(language)

        return res

    @api.model
    def _ubl_add_party_tax_scheme(
        self, commercial_partner, parent_node, ns, version="2.1"
    ):
        res = super()._ubl_add_party_tax_scheme(
            commercial_partner, parent_node, ns, version=version
        )

        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-CR-169: A UBL invoice should not include the
        # AccountingSupplierParty Party PartyTaxScheme RegistrationName
        party = parent_node
        party_tax_scheme = party.find(ns["cac"] + "PartyTaxScheme")
        if party_tax_scheme is not None:
            reg_name = party_tax_scheme.find(ns["cbc"] + "RegistrationName")
            if reg_name is not None:
                party_tax_scheme.remove(reg_name)

        return res

    @api.model
    def _ubl_add_tax_scheme(self, tax_scheme_dict, parent_node, ns, version="2.1"):
        res = super()._ubl_add_tax_scheme(
            tax_scheme_dict, parent_node, ns, version=version
        )

        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-DT-27: Scheme Agency ID attribute should not be present
        party = parent_node

        tax_scheme = party.find(ns["cac"] + "TaxScheme")
        if tax_scheme is not None:
            tax_scheme_id = tax_scheme.find(ns["cbc"] + "ID")
            if tax_scheme_id is not None:
                tax_scheme_id.attrib.pop("schemeAgencyID")

        return res

    @api.model
    def _ubl_add_party_legal_entity(self, partner, parent_node, ns, version="2.1"):
        res = super()._ubl_add_party_legal_entity(
            partner, parent_node, ns, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # PartyLegalEntity/CompanyID must be added just after RegistrationName
        party = parent_node
        legal_entity = party.find(ns["cac"] + "PartyLegalEntity")
        endpoint_dict = partner._get_peppol_endpoint_id()
        endpoint_id = endpoint_dict.get("endpoint_id")
        scheme_id = endpoint_dict.get("scheme_id")
        if scheme_id and endpoint_id:
            company_id_element = etree.SubElement(
                parent_node, ns["cbc"] + "CompanyID", schemeID=scheme_id
            )
            company_id_element.text = endpoint_id
            registration_name = legal_entity.find(ns["cbc"] + "RegistrationName")
            registration_name.addnext(company_id_element)

        # UBL-CR-185: A UBL invoice should not include the AccountingSupplierParty
        #             Party PartyLegalEntity RegistrationAddress
        # UBL-CR-249: A UBL invoice should not include the AccountingCustomerParty
        #             Party PartyLegalEntity RegistrationAddress
        if legal_entity is not None:
            address = legal_entity.find(ns["cac"] + "RegistrationAddress")
            if address is not None:
                legal_entity.remove(address)
        return res

    @api.model
    def _ubl_add_delivery(self, delivery_partner, parent_node, ns, version="2.1"):
        res = super()._ubl_add_delivery(
            delivery_partner, parent_node, ns, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        delivery = parent_node.find(ns["cac"] + "Delivery")
        # UBL-CR-378: A UBL invoice should not include the Delivery DeliveryLocation
        #             Address Country Name
        delivery_location = delivery.find(ns["cac"] + "DeliveryLocation")
        address = delivery_location.find(ns["cac"] + "Address")
        country = address.find(ns["cac"] + "Country")
        country_name = country.find(ns["cbc"] + "Name")
        if country_name is not None:
            country.remove(country_name)
        # UBL-CR-390: A UBL invoice should not include the DeliveryParty EndpointID
        delivery_party = delivery.find(ns["cac"] + "DeliveryParty")
        endpoint_id = delivery_party.find(ns["cbc"] + "EndpointID")
        if endpoint_id is not None:
            delivery_party.remove(endpoint_id)
        # UBL-CR-394: A UBL invoice should not include the DeliveryParty PostalAddress
        postal_address = delivery_party.find(ns["cac"] + "PostalAddress")
        if postal_address is not None:
            delivery_party.remove(postal_address)
        # UBL-CR-396: A UBL invoice should not include the DeliveryParty PartyTaxScheme
        party_tax_scheme = delivery_party.find(ns["cac"] + "PartyTaxScheme")
        if party_tax_scheme is not None:
            delivery_party.remove(party_tax_scheme)
        # UBL-CR-397: A UBL invoice should not include the DeliveryParty
        #             PartyLegalEntity
        party_legal_entity = delivery_party.find(ns["cac"] + "PartyLegalEntity")
        if party_legal_entity is not None:
            delivery_party.remove(party_legal_entity)
        # UBL-CR-398: A UBL invoice should not include the DeliveryParty Contact
        contact = delivery_party.find(ns["cac"] + "Contact")
        if contact is not None:
            delivery_party.remove(contact)
        return res

    @api.model
    def _ubl_add_tax_category(
        self, tax, parent_node, ns, node_name="TaxCategory", version="2.1"
    ):
        res = super()._ubl_add_tax_category(
            tax, parent_node, ns, node_name=node_name, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-CR-597: A UBL invoice should not include the InvoiceLine Item
        #             ClassifiedTaxCategory Name
        tax_category = parent_node.find(ns["cac"] + node_name)
        tax_category_name = tax_category.find(ns["cbc"] + "Name")
        if tax_category_name is not None:
            tax_category.remove(tax_category_name)
        # UBL-CR-679 A UBL invoice should not include the
        #            ClassifiedTaxCategory/ID schemeID
        # UBL-DT-27: Scheme Agency ID attribute should not be present
        tax_category_id = tax_category.find(ns["cbc"] + "ID")
        if tax_category_id is not None:
            tax_category_id.attrib.pop("schemeID", None)
            tax_category_id.attrib.pop("schemeAgencyID", None)
        # BR-E-10B and BR-O-10
        if tax.unece_categ_code in ("E", "O") and node_name == "TaxCategory":
            tax_category_percent = tax_category.find(ns["cbc"] + "Percent")
            tax_exemption_reason = etree.Element(ns["cbc"] + "TaxExemptionReason")
            tax_exemption_reason.text = tax.unece_categ_id.name
            tax_category_percent.addnext(tax_exemption_reason)

        return res

    @api.model
    def _ubl_add_address(self, partner, node_name, parent_node, ns, version="2.1"):
        res = super()._ubl_add_address(
            partner, node_name, parent_node, ns, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-CR-162: A UBL invoice should not include the AccountingSupplierParty
        #             Party PostalAddress CountrySubentityCode
        address = parent_node.find(ns["cac"] + node_name)
        if address is not None:
            subentitycode = address.find(ns["cbc"] + "CountrySubentityCode")
            if subentitycode is not None:
                address.remove(subentitycode)

    def _ubl_add_invoice_line(self, parent_node, iline, line_number, ns, version="2.1"):
        res = super()._ubl_add_invoice_line(
            parent_node, iline, line_number, ns, version=version
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        line_root = parent_node.find(ns["cac"] + "InvoiceLine[last()]")
        invoiced_quantity = line_root.find(ns["cbc"] + "InvoicedQuantity")
        if invoiced_quantity is not None:
            if not invoiced_quantity.attrib.get("unitCode"):
                uom_unece_code = self.company_id.ubl_default_uom_id.unece_code
                if uom_unece_code:
                    invoiced_quantity.attrib["unitCode"] = uom_unece_code
        return res

    def _ubl_add_tax_total(self, xml_root, ns, version="2.1"):
        res = super()._ubl_add_tax_total(xml_root, ns, version=version)
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # BR-CO-18: An Invoice shall at least have one VAT breakdown group (BG-23).
        # PEPPOL-EN16931-R053: Only one tax total with tax subtotals MUST be provided.
        tax_total_node = xml_root.find(ns["cac"] + "TaxTotal")
        if tax_total_node is not None:
            tax_subtotal_node = tax_total_node.find(ns["cac"] + "TaxSubtotal")

            # UBL-CR-499: A UBL invoice should not include the TaxTotal
            # TaxSubtotal Percent
            if tax_subtotal_node is not None:
                tax_perc = tax_subtotal_node.find(ns["cbc"] + "Percent")
                if tax_perc is not None:
                    tax_subtotal_node.remove(tax_perc)

            if tax_subtotal_node is None and self.company_id.ubl_default_tax:
                cur_name = self.currency_id.name
                self._ubl_add_tax_subtotal(
                    self.amount_untaxed,
                    0.0,
                    self.company_id.ubl_default_tax,
                    cur_name,
                    tax_total_node,
                    ns,
                    version=version,
                )

    @api.model
    def _ubl_add_item(
        self,
        name,
        product,
        parent_node,
        ns,
        type="purchase",
        seller=False,
        taxes=None,
        version="2.1",
    ):
        res = super()._ubl_add_item(
            name,
            product,
            parent_node,
            ns,
            type=type,
            seller=seller,
            taxes=taxes,
            version=version,
        )
        if not self.env.context.get("account_invoice_ubl_use_peppol"):
            return res

        # UBL-SR-48: Invoice lines shall have one and only one classified tax category
        item = parent_node.find(ns["cac"] + "Item")
        if item is not None:
            classified_tax_category = item.find(ns["cac"] + "ClassifiedTaxCategory")
            if classified_tax_category is None and self.company_id.ubl_default_tax:
                self._ubl_add_tax_category(
                    self.company_id.ubl_default_tax,
                    item,
                    ns,
                    node_name="ClassifiedTaxCategory",
                    version=version,
                )

    @api.multi
    def _ubl_add_attachments(self, parent_node, ns, version="2.1"):
        super()._ubl_add_attachments(parent_node, ns, version)
        # fix filename of pdf, which is in the form
        # "Invoice-INV/YYYY/####.pdf"
        doc_ref_node = parent_node.find(ns["cac"] + "AdditionalDocumentReference")
        if doc_ref_node is None:
            return
        doc_ref_id_node = doc_ref_node.find(ns["cbc"] + "ID")
        filename = doc_ref_id_node.text.replace("Invoice-", "").replace("/", "_")
        doc_ref_id_node.text = filename
        attachment_node = doc_ref_node.find(ns["cac"] + "Attachment")
        binary_node = attachment_node.find(ns["cbc"] + "EmbeddedDocumentBinaryObject")
        binary_node.attrib["filename"] = filename
