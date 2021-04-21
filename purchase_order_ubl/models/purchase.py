# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "base.ubl"]

    @api.model
    def get_rfq_states(self):
        return ["draft", "sent", "to approve"]

    @api.model
    def get_order_states(self):
        return ["purchase", "done"]

    def _ubl_add_header(self, doc_type, parent_node, ns, version="2.1"):
        if doc_type == "rfq":
            now_utc = fields.Datetime.to_string(fields.Datetime.now())
            date = now_utc[:10]
            time = now_utc[11:]
            currency_node_name = "PricingCurrencyCode"
        elif doc_type == "order":
            date = self.date_approve or self.date_order
            date = fields.Date.to_string(date)
            currency_node_name = "DocumentCurrencyCode"
        ubl_version = etree.SubElement(parent_node, ns["cbc"] + "UBLVersionID")
        ubl_version.text = version
        doc_id = etree.SubElement(parent_node, ns["cbc"] + "ID")
        doc_id.text = self.name
        issue_date = etree.SubElement(parent_node, ns["cbc"] + "IssueDate")
        issue_date.text = date
        if doc_type == "rfq":  # IssueTime is required on RFQ, not on order
            issue_time = etree.SubElement(parent_node, ns["cbc"] + "IssueTime")
            issue_time.text = time
        if self.notes:
            note = etree.SubElement(parent_node, ns["cbc"] + "Note")
            note.text = self.notes
        doc_currency = etree.SubElement(parent_node, ns["cbc"] + currency_node_name)
        doc_currency.text = self.currency_id.name

    def _ubl_add_monetary_total(self, parent_node, ns, version="2.1"):
        monetary_total = etree.SubElement(
            parent_node, ns["cac"] + "AnticipatedMonetaryTotal"
        )
        line_total = etree.SubElement(
            monetary_total,
            ns["cbc"] + "LineExtensionAmount",
            currencyID=self.currency_id.name,
        )
        line_total.text = str(self.amount_untaxed)
        payable_amount = etree.SubElement(
            monetary_total,
            ns["cbc"] + "PayableAmount",
            currencyID=self.currency_id.name,
        )
        payable_amount.text = str(self.amount_total)

    def _ubl_add_rfq_line(self, parent_node, oline, line_number, ns, version="2.1"):
        line_root = etree.SubElement(parent_node, ns["cac"] + "RequestForQuotationLine")
        self._ubl_add_line_item(
            line_number,
            oline.name,
            oline.product_id,
            "purchase",
            oline.product_qty,
            oline.product_uom,
            line_root,
            ns,
            seller=self.partner_id.commercial_partner_id,
            version=version,
        )

    def _ubl_add_order_line(self, parent_node, oline, line_number, ns, version="2.1"):
        line_root = etree.SubElement(parent_node, ns["cac"] + "OrderLine")
        dpo = self.env["decimal.precision"]
        qty_precision = dpo.precision_get("Product Unit of Measure")
        price_precision = dpo.precision_get("Product Price")
        self._ubl_add_line_item(
            line_number,
            oline.name,
            oline.product_id,
            "purchase",
            oline.product_qty,
            oline.product_uom,
            line_root,
            ns,
            seller=self.partner_id.commercial_partner_id,
            currency=self.currency_id,
            price_subtotal=oline.price_subtotal,
            qty_precision=qty_precision,
            price_precision=price_precision,
            version=version,
        )

    def get_delivery_partner(self):
        self.ensure_one()
        if self.dest_address_id:
            return self.dest_address_id
        return self.company_id.partner_id

    def generate_rfq_ubl_xml_etree(self, version="2.1"):
        nsmap, ns = self._ubl_get_nsmap_namespace(
            "RequestForQuotation-2", version=version
        )
        xml_root = etree.Element("RequestForQuotation", nsmap=nsmap)
        doc_type = "rfq"
        self._ubl_add_header(doc_type, xml_root, ns, version=version)

        # The order of SellerSupplierParty / BuyerCustomerParty is different
        # between RFQ and Order !
        self._ubl_add_supplier_party(
            self.partner_id, False, "SellerSupplierParty", xml_root, ns, version=version
        )
        if version == "2.1":
            self._ubl_add_customer_party(
                False,
                self.company_id,
                "BuyerCustomerParty",
                xml_root,
                ns,
                version=version,
            )
        delivery_partner = self.get_delivery_partner()
        self._ubl_add_delivery(delivery_partner, xml_root, ns, version=version)
        if self.incoterm_id:
            self._ubl_add_delivery_terms(
                self.incoterm_id, xml_root, ns, version=version
            )

        for oline in self.order_line:
            # line_number as third arg comes from purchase.order.line id field
            # see https://github.com/OCA/edi/issues/300
            self._ubl_add_rfq_line(xml_root, oline, oline.id, ns, version=version)
        return xml_root

    def generate_order_ubl_xml_etree(self, version="2.1"):
        nsmap, ns = self._ubl_get_nsmap_namespace("Order-2", version=version)
        xml_root = etree.Element("Order", nsmap=nsmap)
        doc_type = "order"
        self._ubl_add_header(doc_type, xml_root, ns, version=version)

        self._ubl_add_customer_party(
            False, self.company_id, "BuyerCustomerParty", xml_root, ns, version=version
        )
        self._ubl_add_supplier_party(
            self.partner_id, False, "SellerSupplierParty", xml_root, ns, version=version
        )
        delivery_partner = self.get_delivery_partner()
        self._ubl_add_delivery(delivery_partner, xml_root, ns, version=version)
        if self.incoterm_id:
            self._ubl_add_delivery_terms(
                self.incoterm_id, xml_root, ns, version=version
            )
        if self.payment_term_id:
            self._ubl_add_payment_terms(
                self.payment_term_id, xml_root, ns, version=version
            )
        self._ubl_add_monetary_total(xml_root, ns, version=version)

        for oline in self.order_line:
            # line_number as third arg comes from purchase.order.line id field
            # see https://github.com/OCA/edi/issues/300
            self._ubl_add_order_line(xml_root, oline, oline.id, ns, version=version)
        return xml_root

    def generate_ubl_xml_string(self, doc_type, version="2.1"):
        """Provide UBL Xml string with no check
        According to your use check this string integrity with
        _ubl_check_xml_schema() method
        """
        self.ensure_one()
        xml_root = self.get_ubl_xml_etree(doc_type, version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )
        logger.debug(
            "%s UBL XML file generated for purchase order ID %d (state %s)",
            doc_type,
            self.id,
            self.state,
        )
        logger.debug(xml_string)
        return xml_string

    def get_ubl_xml_etree(self, doc_type, version="2.1"):
        self.ensure_one()
        assert doc_type in ("order", "rfq"), "wrong doc_type"
        logger.debug("Starting to generate UBL XML %s file", doc_type)
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        if doc_type == "order":
            xml_root = self.with_context(lang=lang).generate_order_ubl_xml_etree(
                version=version
            )
        elif doc_type == "rfq":
            xml_root = self.with_context(lang=lang).generate_rfq_ubl_xml_etree(
                version=version
            )
        return xml_root

    def get_document_name(self, doc_type):
        document = False
        if doc_type == "order":
            document = "Order"
        elif doc_type == "rfq":
            document = "RequestForQuotation"
        return document

    def get_ubl_filename(self, doc_type, version="2.1"):
        """This method is designed to be inherited"""
        if doc_type == "rfq":
            return "UBL-RequestForQuotation-%s.xml" % version
        elif doc_type == "order":
            return "UBL-Order-%s.xml" % version

    def get_ubl_version(self):
        return self.env.context.get("ubl_version", "2.1")

    def get_ubl_lang(self):
        self.ensure_one()
        return self.partner_id.lang or "en_US"

    def add_xml_in_pdf_buffer(self, buffer):
        self.ensure_one()
        doc_type = self.get_ubl_purchase_order_doc_type()
        if doc_type:
            version = self.get_ubl_version()
            xml_filename = self.get_ubl_filename(doc_type, version=version)
            xml_string = self.generate_ubl_xml_string(doc_type, version=version)
            buffer = self._ubl_add_xml_in_pdf_buffer(xml_string, xml_filename, buffer)
        return buffer

    def embed_ubl_xml_in_pdf(self, pdf_content):
        self.ensure_one()
        doc_type = self.get_ubl_purchase_order_doc_type()
        if doc_type:
            version = self.get_ubl_version()
            xml_filename = self.get_ubl_filename(doc_type, version=version)
            xml_string = self.generate_ubl_xml_string(doc_type, version=version)
            self._ubl_check_xml_schema(
                xml_string, self.get_document_name(doc_type), version=version
            )
            pdf_content = self.embed_xml_in_pdf(
                xml_string, xml_filename, pdf_content=pdf_content
            )
        return pdf_content

    def get_ubl_purchase_order_doc_type(self):
        self.ensure_one()
        doc_type = False
        if self.state in self.get_rfq_states():
            doc_type = "rfq"
        elif self.state in self.get_order_states():
            doc_type = "order"
        return doc_type
