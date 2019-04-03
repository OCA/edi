# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from datetime import datetime
from lxml import etree
import logging

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _name = 'account.invoice.import'
    _inherit = ['account.invoice.import', 'base.ubl']

    @api.model
    def parse_xml_invoice(self, xml_root):
        if (
                xml_root.tag and
                xml_root.tag.startswith(
                '{urn:oasis:names:specification:ubl:schema:xsd:Invoice')):
            return self.parse_ubl_invoice(xml_root)
        else:
            return super().parse_xml_invoice(xml_root)

    def get_attachments(self, xml_root, namespaces):
        attach_xpaths = xml_root.xpath(
            "//cac:AdditionalDocumentReference", namespaces=namespaces)
        attachments = {}
        for attach_xpath in attach_xpaths:
            filename_xpath = attach_xpath.xpath(
                "cbc:ID", namespaces=namespaces)
            filename = filename_xpath and filename_xpath[0].text or False
            data_xpath = attach_xpath.xpath(
                "cac:Attachment/cbc:EmbeddedDocumentBinaryObject",
                namespaces=namespaces)
            data_base64 = data_xpath and data_xpath[0].text or False
            if filename and data_base64:
                if (
                        data_xpath[0].attrib and
                        data_xpath[0].attrib.get('mimeCode')):
                    mimetype = data_xpath[0].attrib['mimeCode'].split('/')
                    if len(mimetype) == 2:
                        filename = '%s.%s' % (filename, mimetype[1])
                attachments[filename] = data_base64
        return attachments

    def parse_ubl_invoice_line(self, iline, counters, namespaces):
        price_unit_xpath = iline.xpath(
            "cac:Price/cbc:PriceAmount", namespaces=namespaces)
        qty_xpath = iline.xpath(
            "cbc:InvoicedQuantity", namespaces=namespaces)
        # Some UBL invoices don't have any InvoicedQuantity tag
        # So we have a fallback on quantity = 1
        qty = 1
        uom = {}
        if qty_xpath:
            if float(qty_xpath[0].text):
                qty = float(qty_xpath[0].text)
            if qty_xpath[0].attrib and qty_xpath[0].attrib.get('unitCode'):
                unece_uom = qty_xpath[0].attrib['unitCode']
                if unece_uom == 'ZZ':
                    unece_uom = 'C62'
                uom = {'unece_code': unece_uom}
        product_dict = self.ubl_parse_product(iline, namespaces)
        name_xpath = iline.xpath(
            "cac:Item/cbc:Description", namespaces=namespaces)
        name = name_xpath and name_xpath[0].text or '-'
        price_subtotal_xpath = iline.xpath(
            "cbc:LineExtensionAmount", namespaces=namespaces)
        price_subtotal = float(price_subtotal_xpath[0].text)
        if not price_subtotal:
            return False
        if price_unit_xpath:
            price_unit = float(price_unit_xpath[0].text)
        else:
            price_unit = price_subtotal / qty
        counters['lines'] += price_subtotal
        taxes_xpath = iline.xpath(
            "cac:Item/cac:ClassifiedTaxCategory", namespaces=namespaces)
        if not taxes_xpath:
            taxes_xpath = iline.xpath(
                "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory",
                namespaces=namespaces)
        taxes = []
        for tax in taxes_xpath:
            type_code_xpath = tax.xpath(
                "cac:TaxScheme/cbc:ID[@schemeAgencyID='6']",
                namespaces=namespaces)
            type_code = type_code_xpath and type_code_xpath[0].text or 'VAT'
            categ_code_xpath = tax.xpath(
                "cbc:ID", namespaces=namespaces)
            # TODO: Understand why sometimes they use H
            categ_code = categ_code_xpath and categ_code_xpath[0].text or False
            if categ_code == 'H':
                categ_code = 'S'
            percent_xpath = tax.xpath(
                "cbc:Percent", namespaces=namespaces)
            if not percent_xpath:
                percent_xpath = tax.xpath(
                    "../cbc:Percent", namespaces=namespaces)
            if percent_xpath:
                percentage = percent_xpath[0].text and\
                    float(percent_xpath[0].text)
            else:
                percentage = 0.0
            tax_dict = {
                'amount_type': 'percent',
                'amount': percentage,
                'unece_type_code': type_code,
                'unece_categ_code': categ_code,
                }
            taxes.append(tax_dict)

        vals = {
            'product': product_dict,
            'qty': qty,
            'uom': uom,
            'price_unit': price_unit,
            'price_subtotal': price_subtotal,
            'name': name,
            'taxes': taxes,
            }
        return vals

    @api.model
    def parse_ubl_invoice(self, xml_root):
        """Parse UBL Invoice XML file"""
        namespaces = xml_root.nsmap
        inv_xmlns = namespaces.pop(None)
        namespaces['inv'] = inv_xmlns
        logger.debug('XML file namespaces=%s', namespaces)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        ubl_version_xpath = xml_root.xpath(
            "//cbc:UBLVersionID", namespaces=namespaces)
        ubl_version = ubl_version_xpath and ubl_version_xpath[0].text or '2.1'
        # Check XML schema to avoid headaches trying to import invalid files
        self._ubl_check_xml_schema(xml_string, 'Invoice', version=ubl_version)
        prec = self.env['decimal.precision'].precision_get('Account')
        doc_type_xpath = xml_root.xpath(
            "/inv:Invoice/cbc:InvoiceTypeCode[@listAgencyID='6']",
            namespaces=namespaces)
        inv_type = 'in_invoice'
        if doc_type_xpath:
            inv_type_code = doc_type_xpath[0].text
            if inv_type_code not in ['380', '381']:
                raise UserError(_(
                    "This UBL XML file is not an invoice/refund file "
                    "(InvoiceTypeCode is %s") % inv_type_code)
            if inv_type_code == '381':
                inv_type = 'in_refund'
        inv_number_xpath = xml_root.xpath('//cbc:ID', namespaces=namespaces)
        ord_number_xpath = xml_root.xpath('//cac:OrderReference/cbc:ID',
                                          namespaces=namespaces)
        origin = False
        if ord_number_xpath:
            origin = ord_number_xpath[0].text
        supplier_xpath = xml_root.xpath(
            '/inv:Invoice/cac:AccountingSupplierParty',
            namespaces=namespaces)
        supplier_dict = self.ubl_parse_supplier_party(
            supplier_xpath[0], namespaces)
        customer_xpath_party = xml_root.xpath(
            '/inv:Invoice/cac:AccountingCustomerParty/cac:Party',
            namespaces=namespaces)
        company_dict_full = self.ubl_parse_party(
            customer_xpath_party[0], namespaces)
        company_dict = {}
        # We only take the "official references" for company_dict
        if company_dict_full.get('vat'):
            company_dict = {'vat': company_dict_full['vat']}
        date_xpath = xml_root.xpath(
            '/inv:Invoice/cbc:IssueDate', namespaces=namespaces)
        date_dt = datetime.strptime(date_xpath[0].text, '%Y-%m-%d')
        date_due_xpath = xml_root.xpath(
            "//cbc:PaymentDueDate", namespaces=namespaces)
        date_due_str = False
        if date_due_xpath:
            date_due_dt = datetime.strptime(date_due_xpath[0].text, '%Y-%m-%d')
            date_due_str = fields.Date.to_string(date_due_dt)
        currency_iso_xpath = xml_root.xpath(
            "/inv:Invoice/cbc:DocumentCurrencyCode", namespaces=namespaces)
        total_untaxed_xpath = xml_root.xpath(
            "/inv:Invoice/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
            namespaces=namespaces)
        amount_untaxed = float(total_untaxed_xpath[0].text)
        total_line_xpath = xml_root.xpath(
            "/inv:Invoice/cac:LegalMonetaryTotal/cbc:LineExtensionAmount",
            namespaces=namespaces)
        if total_line_xpath:
            total_line = float(total_line_xpath[0].text)
        else:
            total_line = amount_untaxed
        amount_total_xpath = xml_root.xpath(
            "/inv:Invoice/cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
            namespaces=namespaces)
        if amount_total_xpath:
            amount_total = float(amount_total_xpath[0].text)
        else:
            payable_total = xml_root.xpath(
                "/inv:Invoice/cac:LegalMonetaryTotal/cbc:PayableAmount",
                namespaces=namespaces)
            amount_total = float(payable_total[0].text)
        payment_type_code = xml_root.xpath(
            "/inv:Invoice/cac:PaymentMeans/"
            "cbc:PaymentMeansCode[@listAgencyID='6']",
            namespaces=namespaces)
        iban_xpath = bic_xpath = False
        if payment_type_code and payment_type_code[0].text == '31':
            iban_xpath = xml_root.xpath(
                "//cac:PayeeFinancialAccount/cbc:ID[@schemeID='IBAN']",
                namespaces=namespaces)
            bic_xpath = xml_root.xpath(
                "//cac:PayeeFinancialAccount"
                "/cac:FinancialInstitutionBranch"
                "/cac:FinancialInstitution"
                "/cbc:ID[@schemeID='BIC']",
                namespaces=namespaces)
        attachments = self.get_attachments(xml_root, namespaces)
        res_lines = []
        counters = {'lines': 0.0}
        inv_line_xpath = xml_root.xpath(
            "/inv:Invoice/cac:InvoiceLine", namespaces=namespaces)
        for iline in inv_line_xpath:
            line_vals = self.parse_ubl_invoice_line(
                iline, counters, namespaces)
            if line_vals is False:
                continue
            res_lines.append(line_vals)

        if float_compare(
                total_line, counters['lines'], precision_digits=prec):
            logger.warning(
                "The gloabl LineExtensionAmount (%s) doesn't match the "
                "sum of the amounts of each line (%s). It can "
                "have a diff of a few cents due to sum of rounded values vs "
                "rounded sum policies.", total_line, counters['lines'])

        res = {
            'type': inv_type,
            'partner': supplier_dict,
            'company': company_dict,
            'invoice_number': inv_number_xpath[0].text,
            'origin': origin,
            'date': fields.Date.to_string(date_dt),
            'date_due': date_due_str,
            'currency': {'iso': currency_iso_xpath[0].text},
            'amount_total': amount_total,
            'amount_untaxed': amount_untaxed,
            'iban': iban_xpath and iban_xpath[0].text or False,
            'bic': bic_xpath and bic_xpath[0].text or False,
            'lines': res_lines,
            'attachments': attachments,
            }
        # Hack for the sample UBL invoices that use an invalid VAT number
        if res['partner'].get('vat') in ['NL123456789B01', 'DK16356706']:
            res['partner'].pop('vat')
        # and invalid IBAN
        if res['iban'] == 'NL23ABNA0123456789':
            res.pop('iban')
        logger.info('Result of UBL XML parsing: %s', res)
        return res
