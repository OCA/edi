# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from lxml import etree
from odoo.tools import float_is_zero, float_round
import logging

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'base.ubl']

    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        ubl_version = etree.SubElement(
            parent_node, ns['cbc'] + 'UBLVersionID')
        ubl_version.text = version
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        doc_id.text = self.number
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        issue_date.text = self.date_invoice
        if self.type == 'out_invoice':
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + 'InvoiceTypeCode')
            type_code.text = '380'
        elif self.type == 'out_refund':
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + 'CreditNoteTypeCode')
            type_code.text = '381'
        if self.comment:
            note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note.text = self.comment
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name

    def _ubl_add_order_reference(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        if self.name:
            order_ref = etree.SubElement(
                parent_node, ns['cac'] + 'OrderReference')
            order_ref_id = etree.SubElement(
                order_ref, ns['cbc'] + 'ID')
            order_ref_id.text = self.name

    def _ubl_get_contract_document_reference_dict(self):
        '''Result: dict with key = Doc Type Code, value = ID'''
        self.ensure_one()
        return {}

    def _ubl_add_contract_document_reference(
            self, parent_node, ns, version='2.1'):
        self.ensure_one()
        cdr_dict = self._ubl_get_contract_document_reference_dict()
        for doc_type_code, doc_id in cdr_dict.iteritems():
            cdr = etree.SubElement(
                parent_node, ns['cac'] + 'ContractDocumentReference')
            cdr_id = etree.SubElement(cdr, ns['cbc'] + 'ID')
            cdr_id.text = doc_id
            cdr_type_code = etree.SubElement(
                cdr, ns['cbc'] + 'DocumentTypeCode')
            cdr_type_code.text = doc_type_code

    def _ubl_add_attachments(self, parent_node, ns, version='2.1'):
        if (
                self.company_id.embed_pdf_in_ubl_xml_invoice and
                not self._context.get('no_embedded_pdf')):
            filename = 'Invoice-' + self.number + '.pdf'
            docu_reference = etree.SubElement(
                parent_node, ns['cac'] + 'AdditionalDocumentReference')
            docu_reference_id = etree.SubElement(
                docu_reference, ns['cbc'] + 'ID')
            docu_reference_id.text = filename
            attach_node = etree.SubElement(
                docu_reference, ns['cac'] + 'Attachment')
            binary_node = etree.SubElement(
                attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
                mimeCode="application/pdf", filename=filename)
            ctx = self._context.copy()
            ctx['no_embedded_ubl_xml'] = True
            pdf_inv = self.env["report"].get_pdf(
                [self.id], "account.report_invoice")
            binary_node.text = pdf_inv.encode('base64')

    def _ubl_get_invoice_vat_exclusive_amount(self):
        amount = self.amount_untaxed
        # Add also non-VAT taxes that are not subjected to VAT
        for invoice_tax in self.tax_line_ids:
            tax = invoice_tax.tax_id
            if tax.unece_type_id.code != "VAT":
                amount += invoice_tax.amount
        return amount

    def _ubl_get_invoice_vat_amount(self):
        amount = self.amount_tax
        # Add also non-VAT taxes that are not subjected to VAT
        for invoice_tax in self.tax_line_ids:
            tax = invoice_tax.tax_id
            if tax.unece_type_id.code != "VAT":
                amount -= invoice_tax.amount
        return amount

    def _ubl_get_charge_total_amount(self):
        amount = 0.0
        for tline in self.tax_line_ids:
            if tline.tax_id.unece_type_id.code != "VAT":
                if not tline.tax_id.include_base_amount:
                    # For non-VAT taxes, not subject to VAT, they are declared
                    # as AllowanceCharge
                    amount += tline.amount
        return amount

    def _ubl_add_legal_monetary_total(self, parent_node, ns, version='2.1'):
        monetary_total = etree.SubElement(
            parent_node, ns['cac'] + 'LegalMonetaryTotal')
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        line_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_total.text = '%0.*f' % (prec, self.amount_untaxed)
        tax_excl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxExclusiveAmount',
            currencyID=cur_name)
        tax_excl_total.text = "%0.*f" % (
            prec, self._ubl_get_invoice_vat_exclusive_amount())
        tax_incl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxInclusiveAmount',
            currencyID=cur_name)
        tax_incl_total.text = '%0.*f' % (prec, self.amount_total)
        charge_total_amount = self._ubl_get_charge_total_amount()
        if charge_total_amount:
            el_charge_total_amount = etree.SubElement(
                monetary_total, ns["cbc"] + "ChargeTotalAmount",
                currencyID=cur_name)
            el_charge_total_amount.text = "%0.*f" % (
                prec, charge_total_amount)
        prepaid_amount = etree.SubElement(
            monetary_total, ns['cbc'] + 'PrepaidAmount',
            currencyID=cur_name)
        prepaid_value = self.amount_total - self.residual
        prepaid_amount.text = '%0.*f' % (prec, prepaid_value)
        payable_amount = etree.SubElement(
            monetary_total, ns['cbc'] + 'PayableAmount',
            currencyID=cur_name)
        payable_amount.text = '%0.*f' % (prec, self.residual)

    def _ubl_get_invoice_line_price_unit(self, iline):
        """Compute the base unit price without taxes"""
        price = iline.price_unit
        qty = 1.0
        if iline.invoice_line_tax_ids:
            tax_incl = any(t.price_include for t in iline.invoice_line_tax_ids)
            if tax_incl:
                # To prevent rounding issue, we must declare tax excluded price
                # for the total quantity
                qty = iline.quantity
            taxes = iline.invoice_line_tax_ids.compute_all(
                price, self.currency_id, qty, product=iline.product_id,
                partner=self.partner_id)
            if taxes:
                price = taxes['total_excluded']
        dpo = self.env["decimal.precision"]
        price_precision = dpo.precision_get("Product Price")
        return price, price_precision, qty

    def _ubl_get_invoice_line_discount(self, iline, base_price, base_qty):
        # Formula: Net amount = Invoiced quantity * (Item net price/item price
        #   base quantity) + Sum of invoice line charge amount - sum of invoice
        #   line allowance amount
        discount = iline.quantity / base_qty * base_price - iline.price_subtotal
        dpo = self.env["decimal.precision"]
        price_precision = dpo.precision_get("Product Price")
        discount = float_round(discount, precision_digits=price_precision)
        return discount, price_precision

    def _ubl_add_invoice_line_discount(self, xml_root, iline, base_price, base_qty, ns, version='2.1'):
        discount, prec = self._ubl_get_invoice_line_discount(iline, base_price, base_qty)
        if float_is_zero(discount, precision_digits=prec):
            return
        charge_node = etree.SubElement(xml_root, ns["cac"] + "AllowanceCharge")
        charge_indicator_node = etree.SubElement(charge_node, ns["cbc"] + "ChargeIndicator")
        charge_indicator_node.text = "false"
        charge_reason_code_node = etree.SubElement(charge_node, ns["cbc"] + "AllowanceChargeReasonCode")
        charge_reason_code_node.text = "95"
        charge_reason_node = etree.SubElement(charge_node, ns["cbc"] + "AllowanceChargeReason")
        charge_reason_node.text = "Discount"
        charge_amount_node = etree.SubElement(
            charge_node, ns["cbc"] + "Amount", currencyID=self.currency_id.name)
        charge_amount_node.text = "%0.*f" % (prec, discount)

    def _ubl_add_invoice_line(
            self, parent_node, iline, line_number, ns, version='2.1'):
        cur_name = self.currency_id.name
        if self.type == 'out_invoice':
            line_root = etree.SubElement(
                parent_node, ns['cac'] + 'InvoiceLine')
        elif self.type == 'out_refund':
            line_root = etree.SubElement(
                parent_node, ns['cac'] + 'CreditNoteLine')
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        account_precision = self.currency_id.decimal_places
        line_id = etree.SubElement(line_root, ns['cbc'] + 'ID')
        line_id.text = unicode(line_number)
        uom_unece_code = False
        # uom_id is not a required field on account.invoice.line
        if iline.uom_id and iline.uom_id.unece_code:
            uom_unece_code = iline.uom_id.unece_code
        if self.type == 'out_invoice':
            qty_element_name = "InvoicedQuantity"
        elif self.type == 'out_refund':
            qty_element_name = "CreditedQuantity"
        if uom_unece_code:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + qty_element_name,
                unitCode=uom_unece_code)
        else:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + qty_element_name)
        qty = iline.quantity
        quantity.text = '%0.*f' % (qty_precision, qty)
        base_price, price_precision, base_qty = self._ubl_get_invoice_line_price_unit(iline)
        line_amount = etree.SubElement(
            line_root, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_amount.text = '%0.*f' % (account_precision, iline.price_subtotal)
        self._ubl_add_invoice_line_discount(
            line_root, iline, base_price, base_qty, ns, version=version)
        self._ubl_add_item(
            iline.name, iline.product_id, line_root, ns, type='sale',
            version=version)
        price_node = etree.SubElement(line_root, ns['cac'] + 'Price')
        price_amount = etree.SubElement(
            price_node, ns['cbc'] + 'PriceAmount', currencyID=cur_name)
        price_amount.text = '%0.*f' % (price_precision, base_price)
        if uom_unece_code:
            base_qty_node = etree.SubElement(
                price_node, ns['cbc'] + 'BaseQuantity',
                unitCode=uom_unece_code)
        else:
            base_qty_node = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity')
        base_qty_node.text = '%0.*f' % (qty_precision, base_qty)

    def _ubl_add_invoice_line_tax_total(
            self, iline, parent_node, ns, version='2.1'):
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        tax_total_node = etree.SubElement(parent_node, ns['cac'] + 'TaxTotal')
        # Peppol BIS Billing 3.0 supports only VAT taxes
        # Other taxes must be defined as AllowanceCharge
        vat_taxes = iline.invoice_line_tax_ids.filtered(
            lambda t: t.unece_type_id.code == "VAT")
        res_taxes = vat_taxes.compute_all(
            iline.price_subtotal, quantity=1, product=iline.product_id,
            partner=self.partner_id)
        tax_total = float_round(
            res_taxes['total_included'] - res_taxes['total_excluded'],
            precision_digits=prec)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = '%0.*f' % (prec, tax_total)
        if not float_is_zero(tax_total, precision_digits=prec):
            for res_tax in res_taxes['taxes']:
                tax = self.env['account.tax'].browse(res_tax['id'])
                self._ubl_add_tax_subtotal(
                    iline.price_subtotal, res_tax["amount"], tax, cur_name,
                    tax_total_node, ns, version=version)

    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        self.ensure_one()
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        for tline in self.tax_line_ids:
            if tline.tax_id.unece_type_id.code != "VAT":
                if not tline.tax_id.include_base_amount:
                    # For non-VAT taxes, not subject to VAT, declare as AllowanceCharge
                    charge_node = etree.SubElement(xml_root, ns["cac"] + "AllowanceCharge")
                    charge_indicator_node = etree.SubElement(charge_node, ns["cbc"] + "ChargeIndicator")
                    charge_indicator_node.text = "true"
                    charge_reason_code_node = etree.SubElement(charge_node, ns["cbc"] + "AllowanceChargeReasonCode")
                    charge_reason_code_node.text = "ABK"
                    charge_reason_node = etree.SubElement(charge_node, ns["cbc"] + "AllowanceChargeReason")
                    charge_reason_node.text = "Miscellaneous"
                    charge_amount_node = etree.SubElement(
                        charge_node, ns["cbc"] + "Amount", currencyID=cur_name)
                    charge_amount_node.text = '%0.*f' % (prec, tline.amount)
                    self._ubl_add_tax_category(tline.tax_id, charge_node, ns, version=version)
        tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = "%0.*f" % (prec, self._ubl_get_invoice_vat_amount())
        if not float_is_zero(self.amount_tax, precision_digits=prec):
            exempt = 0.0
            exempt_taxes = []
            for tline in self.tax_line_ids:
                if tline.tax_id.unece_type_id.code == "VAT":
                    self._ubl_add_tax_subtotal(
                        tline.base, tline.amount, tline.tax_id, cur_name,
                        tax_total_node, ns, version=version)
                elif not tline.tax_id.include_base_amount:
                    # For non-VAT taxes, not subject to VAT, declare as VAT exempted
                    # Only one exempt line is allowed, regroup if multiple
                    exempt += tline.amount
                    exempt_taxes.append(tline.tax_id)
            if not float_is_zero(exempt, precision_digits=prec):
                self._ubl_add_tax_subtotal(
                    exempt, 0, exempt_taxes[0], cur_name,
                    tax_total_node, ns, version=version)
                if len(exempt_taxes) > 1:
                    # xpath cac:TaxCategory/cbc:Name
                    exempt_node = tax_total_node[-1]
                    exempt_node = [e for e in list(exempt_node) if e.tag == ns["cac"] + "TaxCategory"][0]
                    exempt_node = [e for e in list(exempt_node) if e.tag == ns["cbc"] + "Name"][0]
                    exempt_node.text = " + ".join([e.name for e in exempt_taxes])

    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        if self.type == 'out_invoice':
            nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
            xml_root = etree.Element('Invoice', nsmap=nsmap)
        elif self.type == 'out_refund':
            nsmap, ns = self._ubl_get_nsmap_namespace('CreditNote-2', version=version)
            xml_root = etree.Element('CreditNote', nsmap=nsmap)
        self._ubl_add_header(xml_root, ns, version=version)
        self._ubl_add_order_reference(xml_root, ns, version=version)
        self._ubl_add_contract_document_reference(
            xml_root, ns, version=version)
        self._ubl_add_attachments(xml_root, ns, version=version)
        self._ubl_add_supplier_party(
            False, self.company_id, 'AccountingSupplierParty', xml_root, ns,
            version=version)
        self._ubl_add_customer_party(
            self.partner_id, False, 'AccountingCustomerParty', xml_root, ns,
            version=version)
        # the field 'partner_shipping_id' is defined in the 'sale' module
        if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
            self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
        # Put paymentmeans block even when invoice is paid ?
        payment_identifier = self.get_payment_identifier()
        self._ubl_add_payment_means(
            self.partner_bank_id, self.payment_mode_id, self.date_due,
            xml_root, ns, payment_identifier=payment_identifier,
            version=version)
        if self.payment_term_id:
            self._ubl_add_payment_terms(
                self.payment_term_id, xml_root, ns, version=version)
        self._ubl_add_tax_total(xml_root, ns, version=version)
        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        for iline in self.invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(
                xml_root, iline, line_number, ns, version=version)
        return xml_root

    def generate_ubl_xml_string(self, version='2.1'):
        self.ensure_one()
        assert self.state in ('open', 'paid')
        assert self.type in ('out_invoice', 'out_refund')
        logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        xml_root = self.with_context(lang=lang).\
            generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        if self.type == 'out_invoice':
            self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
        elif self.type == 'out_refund':
            self._ubl_check_xml_schema(xml_string, 'CreditNote', version=version)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID %d '
            '(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string

    def get_ubl_filename(self, version='2.1'):
        """This method is designed to be inherited"""
        if self.type == 'out_invoice':
            return 'UBL-Invoice-%s.xml' % version
        elif self.type == 'out_refund':
            return 'UBL-CreditNote-%s.xml' % version

    def get_ubl_version(self):
        version = self._context.get('ubl_version') or '2.1'
        return version

    def get_ubl_lang(self):
        return self.partner_id.lang or 'en_US'

    def embed_ubl_xml_in_pdf(self, pdf_content=None, pdf_file=None):
        self.ensure_one()
        if (
                self.type in ('out_invoice', 'out_refund') and
                self.state in ('open', 'paid')):
            version = self.get_ubl_version()
            ubl_filename = self.get_ubl_filename(version=version)
            xml_string = self.generate_ubl_xml_string(version=version)
            pdf_content = self.embed_xml_in_pdf(
                xml_string, ubl_filename,
                pdf_content=pdf_content, pdf_file=pdf_file)
        return pdf_content

    def attach_ubl_xml_file_button(self):
        self.ensure_one()
        assert self.type in ('out_invoice', 'out_refund')
        assert self.state in ('open', 'paid')
        version = self.get_ubl_version()
        xml_string = self.generate_ubl_xml_string(version=version)
        filename = self.get_ubl_filename(version=version)
        attach = self.env['ir.attachment'].create({
            'name': filename,
            'res_id': self.id,
            'res_model': unicode(self._name),
            'datas': xml_string.encode('base64'),
            'datas_fname': filename,
            # I have default_type = 'out_invoice' in context, so 'type'
            # would take 'out_invoice' value by default !
            'type': 'binary',
            })
        action = self.env['ir.actions.act_window'].for_xml_id(
            'base', 'action_attachment')
        action.update({
            'res_id': attach.id,
            'views': False,
            'view_mode': 'form,tree'
            })
        return action
