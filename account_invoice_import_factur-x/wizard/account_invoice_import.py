# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from lxml import etree
import logging

logger = logging.getLogger(__name__)

try:
    from facturx import get_facturx_flavor, get_facturx_level
except ImportError:
    logger.debug('Cannot import facturx')


class AccountInvoiceImport(models.TransientModel):
    _name = 'account.invoice.import'
    _inherit = ['account.invoice.import', 'base.facturx']

    @api.model
    def parse_xml_invoice(self, xml_root):
        if (
                xml_root.tag and
                'crossindustry' in xml_root.tag.lower() and
                'invoice' in xml_root.tag.lower()):
            return self.parse_facturx_invoice(xml_root)
        else:
            return super(AccountInvoiceImport, self).parse_xml_invoice(
                xml_root)

    @api.model
    def parse_facturx_taxes(self, taxes_xpath, namespaces):
        taxes = []
        for tax in taxes_xpath:
            type_code = self.multi_xpath_helper(
                tax, ["ram:TypeCode"], namespaces) or 'VAT'
            # CategoryCode not available at Basic level
            categ_code = self.multi_xpath_helper(
                tax, ["ram:CategoryCode"], namespaces)
            percentage = self.multi_xpath_helper(
                tax,
                ["ram:RateApplicablePercent",  # Factur-X
                 "ram:ApplicablePercent",  # ZUGFeRD
                 ], namespaces, isfloat=True) or 0.0
            due_date_code = self.multi_xpath_helper(
                tax, ["ram:DueDateTypeCode"], namespaces)
            if due_date_code == '29':
                due_date_code = '5'
            taxes.append({
                'amount_type': 'percent',
                'amount': percentage,
                'unece_type_code': type_code,
                'unece_categ_code': categ_code,
                'unece_due_date_code': due_date_code,
                })
        return taxes

    @api.model
    def parse_facturx_allowance_charge(
            self, acline, global_taxes, label_suffix, ac_qty_dict, counters,
            namespaces):
        # This method is designed to work for global AND line charges/allowance
        acentry = {}
        reason = self.multi_xpath_helper(acline, ["ram:Reason"], namespaces)
        if reason:
            acentry['name'] = reason
        # ChargeIndicator and ActualAmount are required field
        acentry['price_unit'] = self.multi_xpath_helper(
            acline, ['ram:ActualAmount'], namespaces, isfloat=True)
        ch_indic = self.multi_xpath_helper(
            acline, ["ram:ChargeIndicator/udt:Indicator"], namespaces)
        if ch_indic == 'false':  # allowance
            acentry['qty'] = ac_qty_dict['allowances']
            acentry['product'] = {'code': 'EDI-ALLOWANCE'}
            if 'allowances' in counters:
                counters['allowances'] += acentry['price_unit']
            if not acentry.get('name'):
                acentry['name'] = _('Misc Allowance')
        elif ch_indic == 'true':  # charge
            acentry['qty'] = ac_qty_dict['charges']
            acentry['product'] = {'code': 'EDI-CHARGE'}
            if 'charges' in counters:
                counters['charges'] += acentry['price_unit']
            if not acentry.get('name'):
                acentry['name'] = _('Misc Charge')
        else:
            raise UserError(_('Unknown ChargeIndicator %s', ch_indic))
        acentry['name'] = u'%s (%s)' % (acentry['name'], label_suffix)
        taxes_xpath = self.raw_multi_xpath_helper(
            acline, ["ram:CategoryTradeTax"], namespaces)
        if taxes_xpath:
            acentry['taxes'] = self.parse_facturx_taxes(
                taxes_xpath, namespaces)
        else:
            acentry['taxes'] = global_taxes
        return acentry

    @api.model
    def parse_facturx_invoice_line(
            self, iline, global_taxes, ac_qty_dict, counters, namespaces):
        xpath_dict = {
            'product': {
                'barcode': ["ram:SpecifiedTradeProduct/ram:GlobalID"],
                'code': ["ram:SpecifiedTradeProduct/ram:SellerAssignedID"],
                },
            'name': ["ram:SpecifiedTradeProduct/ram:Name"],
            'date_start': [
                "ram:SpecifiedLineTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:StartDateTime/udt:DateTimeString"],
            'date_end': [
                "ram:SpecifiedLineTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:EndDateTime/udt:DateTimeString"],
            }
        vals = self.xpath_to_dict_helper(iline, xpath_dict, namespaces)
        price_unit_xpath = iline.xpath(
            "ram:SpecifiedSupplyChainTradeAgreement"
            "/ram:NetPriceProductTradePrice"
            "/ram:ChargeAmount",
            namespaces=namespaces)
        qty_xpath_list = [
            "ram:SpecifiedLineTradeDelivery/ram:BilledQuantity",  # Factur-X
            "ram:SpecifiedSupplyChainTradeDelivery/ram:BilledQuantity",  # ZF
            ]
        qty = self.multi_xpath_helper(
            iline, qty_xpath_list, namespaces, isfloat=True)
        if not qty:
            return False
        uom = {}
        qty_xpath = self.raw_multi_xpath_helper(
            iline, qty_xpath_list, namespaces)
        if qty_xpath[0].attrib and qty_xpath[0].attrib.get('unitCode'):
            unece_uom = qty_xpath[0].attrib['unitCode']
            uom = {'unece_code': unece_uom}
        price_subtotal = self.multi_xpath_helper(
            iline,
            ["ram:SpecifiedLineTradeSettlement"
             "/ram:SpecifiedTradeSettlementLineMonetarySummation"
             "/ram:LineTotalAmount",  # Factur-X
             "ram:SpecifiedSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeSettlementMonetarySummation"
             "/ram:LineTotalAmount",  # ZUGFeRD
             ], namespaces, isfloat=True)
        if price_unit_xpath:
            price_unit = float(price_unit_xpath[0].text)
        else:
            price_unit = price_subtotal / qty
        counters['lines'] += price_subtotal
        # Reminder : ApplicableTradeTax not available on lines
        # at Basic level
        taxes_xpath = self.raw_multi_xpath_helper(
            iline,
            ["ram:SpecifiedLineTradeSettlement"
             "/ram:ApplicableTradeTax",  # Factur-X
             "ram:SpecifiedSupplyChainTradeSettlement"
             "//ram:ApplicableTradeTax",  # ZUGFeRD
             ], namespaces)
        taxes = self.parse_facturx_taxes(taxes_xpath, namespaces)
        vals.update({
            'qty': qty,
            'uom': uom,
            'price_unit': price_unit,
            'price_subtotal': price_subtotal,
            'taxes': taxes or global_taxes,
            })
        iline_allowance_charge_xpath = self.raw_multi_xpath_helper(
            iline,
            ["ram:SpecifiedLineTradeSettlement"
             "/ram:SpecifiedTradeAllowanceCharge",  # Factur-X
             ], namespaces)
        res = [vals]
        for ac_element in iline_allowance_charge_xpath:
            acentry = self.parse_facturx_allowance_charge(
                ac_element, taxes or global_taxes, vals['name'], ac_qty_dict,
                {}, namespaces)
            counters['lines'] += acentry['price_unit'] * acentry['qty']
            res.append(acentry)
        return res

    @api.model
    def parse_facturx_invoice(self, xml_root):
        """Parse Cross Industry Invoice XML file"""
        logger.debug('Starting to parse XML file as Factur-X/ZUGFeRD file')
        namespaces = xml_root.nsmap
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        try:
            flavor = get_facturx_flavor(xml_root)
        except Exception:
            raise UserError(_(
                "Could not detect if the invoice is a Factur-X or ZUGFeRD "
                "invoice."))
        doc_id = self.multi_xpath_helper(
            xml_root,
            ["//rsm:ExchangedDocumentContext"
             "/ram:GuidelineSpecifiedDocumentContextParameter"
             "/ram:ID",  # Factur-X
             "//rsm:SpecifiedExchangedDocumentContext"
             "/ram:GuidelineSpecifiedDocumentContextParameter"
             "/ram:ID",  # ZUGFeRD
             ], namespaces)
        if flavor == 'factur-x':
            level = get_facturx_level(xml_root)
        else:
            level = doc_id.split(':')[-1]
        # Check XML schema to avoid headaches trying to import invalid files
        self._cii_check_xml_schema(xml_string, flavor, level=level)
        prec = self.env['decimal.precision'].precision_get('Account')
        logger.debug('XML file namespaces=%s', namespaces)
        doc_type = self.multi_xpath_helper(
            xml_root,
            ['//rsm:ExchangedDocument/ram:TypeCode',  # Factur-X
             '//rsm:HeaderExchangedDocument/ram:TypeCode',  # ZUGFeRD
             ], namespaces)
        if doc_type == '380':
            inv_type = 'in_invoice'
            # Reminder: the module account_invoice_import supports
            # refunds with type == 'in_invoice' and negative amounts and qty
            # It will convert it to type = 'in_refund' and positive amounts/qty
        elif doc_type == '381':
            inv_type = 'in_refund'
        else:
            raise UserError(_(
                "For the moment, in the Factur-X import, we only support "
                "type code 380 and 381. (TypeCode is %s)") % doc_type)

        xpath_dict = {
            'partner': {
                'vat': [
                    "//ram:ApplicableHeaderTradeAgreement"
                    "/ram:SellerTradeParty"
                    "/ram:SpecifiedTaxRegistration"
                    "/ram:ID[@schemeID='VA']",  # Factur-X
                    "//ram:ApplicableSupplyChainTradeAgreement"
                    "/ram:SellerTradeParty"
                    "/ram:SpecifiedTaxRegistration"
                    "/ram:ID[@schemeID='VA']",  # ZUGFeRD
                    ],
                'name': [
                    '//ram:ApplicableHeaderTradeAgreement'
                    '/ram:SellerTradeParty'
                    '/ram:Name',  # Factur-X
                    '//ram:ApplicableSupplyChainTradeAgreement'
                    '/ram:SellerTradeParty'
                    '/ram:Name',  # ZUGFeRD
                    ],
                'email': [
                    "//ram:ApplicableHeaderTradeAgreement"
                    "/ram:SellerTradeParty"
                    "/ram:DefinedTradeContact"
                    "/ram:EmailURIUniversalCommunication"
                    "/ram:URIID",  # Factur-X
                    "//ram:ApplicableSupplyChainTradeAgreement"
                    "/ram:SellerTradeParty"
                    "/ram:DefinedTradeContact"
                    "/ram:EmailURIUniversalCommunication"
                    "/ram:URIID",  # ZUGFeRD
                    ],
                },
            'invoice_number': [
                '//rsm:ExchangedDocument/ram:ID',  # Factur-X
                '//rsm:HeaderExchangedDocument/ram:ID',  # ZUGFeRD
                ],
            'date': [
                '//rsm:ExchangedDocument'
                '/ram:IssueDateTime/udt:DateTimeString',  # Factur-X
                '//rsm:HeaderExchangedDocument'
                '/ram:IssueDateTime/udt:DateTimeString',  # ZUGFeRD
                ],
            'date_due': [
                "//ram:ApplicableHeaderTradeSettlement"
                "/ram:SpecifiedTradePaymentTerms"
                "/ram:DueDateDateTime"
                "/udt:DateTimeString",  # Factur-X
                "//ram:ApplicableSupplyChainTradeSettlement"
                "/ram:SpecifiedTradePaymentTerms"
                "/ram:DueDateDateTime"
                "/udt:DateTimeString",  # ZUGFeRD
                ],
            'date_start': [
                "//ram:ApplicableHeaderTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:StartDateTime/udt:DateTimeString",
                "//ram:ApplicableSupplyChainTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:StartDateTime/udt:DateTimeString",
                ],
            'date_end': [
                "//ram:ApplicableHeaderTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:EndDateTime/udt:DateTimeString",
                "//ram:ApplicableSupplyChainTradeSettlement"
                "/ram:BillingSpecifiedPeriod"
                "/ram:EndDateTime/udt:DateTimeString",
                ],
            'currency': {
                'iso': [
                    "//ram:ApplicableHeaderTradeSettlement"
                    "/ram:InvoiceCurrencyCode",  # Factur-X
                    "//ram:ApplicableSupplyChainTradeSettlement"
                    "/ram:InvoiceCurrencyCode",  # ZUGFeRD
                    ],
                },
            'amount_total': [
                "//ram:ApplicableHeaderTradeSettlement"
                "/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
                "/ram:GrandTotalAmount",  # Factur-X
                "//ram:ApplicableSupplyChainTradeSettlement"
                "/ram:SpecifiedTradeSettlementMonetarySummation"
                "/ram:GrandTotalAmount",  # ZUGFeRD
                ],
            }
        res = self.xpath_to_dict_helper(xml_root, xpath_dict, namespaces)
        amount_total = res['amount_total']
        ac_qty_dict = {
            'charges': 1,
            'allowances': -1}
        if (
                float_compare(amount_total, 0, precision_digits=prec) < 0 and
                inv_type == 'in_invoice'):
            ac_qty_dict = {
                'charges': -1,
                'allowances': 1}

        total_line = self.multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
             "/ram:LineTotalAmount",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeSettlementMonetarySummation"
             "/ram:LineTotalAmount",  # ZUGFeRD
             ], namespaces, isfloat=True)
        # reminder : total_line is not present in MINIMUM profile
        total_charge = self.multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
             "/ram:ChargeTotalAmount",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeSettlementMonetarySummation"
             "/ram:ChargeTotalAmount",  # ZUGFeRD
             ], namespaces, isfloat=True)
        total_tradeallowance = self.multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
             "/ram:AllowanceTotalAmount",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeSettlementMonetarySummation"
             "/ram:AllowanceTotalAmount",  # ZUGFeRD
             ], namespaces, isfloat=True)
        amount_tax = self.multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
             "/ram:TaxTotalAmount",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeSettlementMonetarySummation"
             "/ram:TaxTotalAmount",  # ZUGFeRD
             ], namespaces, isfloat=True)
        # Check coherence
        if total_line:
            check_total = total_line + total_charge - total_tradeallowance\
                + amount_tax
            if float_compare(check_total, amount_total, precision_digits=prec):
                raise UserError(_(
                    "The GrandTotalAmount is %s but the sum of "
                    "the lines plus the total charge plus the total trade "
                    "allowance plus the total taxes is %s.")
                    % (amount_total, check_total))

        amount_untaxed = amount_total - amount_tax
        payment_type_code = self.multi_xpath_helper(
            xml_root,
            ["//ram:SpecifiedTradeSettlementPaymentMeans/ram:TypeCode"],
            namespaces)  # ZUGFeRD and Factur-X
        iban = bic = False
        if payment_type_code and payment_type_code in ('30', '31'):
            iban = self.multi_xpath_helper(
                xml_root,
                ["//ram:SpecifiedTradeSettlementPaymentMeans"
                 "/ram:PayeePartyCreditorFinancialAccount"
                 "/ram:IBANID"], namespaces)  # ZUGFeRD and Factur-X
            bic = self.multi_xpath_helper(
                xml_root,
                ["//ram:SpecifiedTradeSettlementPaymentMeans"
                 "/ram:PayeeSpecifiedCreditorFinancialInstitution"
                 "/ram:BICID"], namespaces)  # ZUGFeRD and Factur-X
        # global_taxes only used as fallback when taxes are not detailed
        # on invoice lines (which is the case at Basic level)
        global_taxes_xpath = self.raw_multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:ApplicableTradeTax",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:ApplicableTradeTax",  # ZUGFeRD
             ], namespaces)
        global_taxes = self.parse_facturx_taxes(global_taxes_xpath, namespaces)
        logger.debug('global_taxes=%s', global_taxes)
        res_lines = []
        counters = {
            'allowances': 0.0,
            'charges': 0.0,
            'lines': 0.0,
            }

        inv_line_xpath = self.raw_multi_xpath_helper(
            xml_root, ["//ram:IncludedSupplyChainTradeLineItem"], namespaces)
        for iline in inv_line_xpath:
            line_list = self.parse_facturx_invoice_line(
                iline, global_taxes, ac_qty_dict, counters, namespaces)
            if line_list is False:
                continue
            res_lines += line_list

        if float_compare(
                total_line, counters['lines'], precision_digits=prec):
            logger.warning(
                "The global LineTotalAmount (%s) doesn't match the "
                "sum of the LineTotalAmount of each line (%s). It can "
                "have a diff of a few cents due to sum of rounded values vs "
                "rounded sum policies.", total_line, counters['lines'])

        # In Factur-X, "SpecifiedTradeAllowanceCharge" is used both for
        # charges (<ram:ChargeIndicator> = TRUE, counted in ChargeTotalAmount)
        # and for allowance (<ram:ChargeIndicator> = False, counted in
        # AllowanceTotalAmount)
        global_allowance_charge_xpath = self.raw_multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeAllowanceCharge",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeAllowanceCharge",  # ZUGFeRD
             ], namespaces)
        for ac_element in global_allowance_charge_xpath:
            acentry = self.parse_facturx_allowance_charge(
                ac_element, global_taxes, _('Global'), ac_qty_dict, counters,
                namespaces)
            res_lines.append(acentry)

        # These LogisticsServiceCharge lines don't seem to exist in Factur-X
        # but we keep them for ZUGFeRD
        charge_line_xpath = self.raw_multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedLogisticsServiceCharge",  # ZUGFeRD
             ], namespaces)
        for chline in charge_line_xpath:
            name = self.multi_xpath_helper(
                chline, ["ram:Description"], namespaces)\
                or _("Logistics Service")
            price_unit = self.multi_xpath_helper(
                chline, ["ram:AppliedAmount"], namespaces, isfloat=True)
            counters['charges'] += price_unit
            taxes_xpath = self.raw_multi_xpath_helper(
                chline, ["ram:AppliedTradeTax"], namespaces)
            taxes = self.parse_facturx_taxes(taxes_xpath, namespaces)
            vals = {
                'name': name,
                'qty': ac_qty_dict['charges'],
                'price_unit': price_unit,
                'taxes': taxes or global_taxes,
                }
            res_lines.append(vals)

        if float_compare(
                total_charge, counters['charges'], precision_digits=prec):
            if (
                    len(global_taxes) <= 1 and
                    float_is_zero(counters['charges'], precision_digits=prec)):
                res_lines.append({
                    'name': _("Misc Global Charge"),
                    'qty': ac_qty_dict['charges'],
                    'price_unit': total_charge,
                    'taxes': global_taxes,
                    })
            else:
                raise UserError(_(
                    "ChargeTotalAmount (%s) doesn't match the "
                    "total of the charge lines (%s). Maybe it is "
                    "because the Factur-X XML file is at BASIC level, "
                    "and we don't have the details of taxes for the "
                    "charge lines.")
                    % (total_charge, counters['charges']))

        if float_compare(
                abs(total_tradeallowance), counters['allowances'],
                precision_digits=prec):
            if (
                    len(global_taxes) <= 1 and
                    float_is_zero(
                        counters['allowances'], precision_digits=prec)):
                res_lines.append({
                    'name': _("Misc Global Allowance"),
                    'qty': ac_qty_dict['allowances'],
                    'price_unit': total_tradeallowance,
                    'taxes': global_taxes,
                    })
            else:
                raise UserError(_(
                    "AllowanceTotalAmount (%s) doesn't match the "
                    "total of the allowance lines (%s). Maybe it is "
                    "because the Factur-X XML file is at BASIC level, "
                    "and we don't have the details of taxes for the "
                    "allowance lines.")
                    % (abs(total_tradeallowance), counters['allowances']))

        res.update({
            'type': inv_type,
            'amount_total': amount_total,
            'amount_untaxed': amount_untaxed,
            'iban': iban,
            'bic': bic,
            'lines': res_lines,
            })
        # Hack for the sample ZUGFeRD invoices that use an invalid VAT number !
        if res['partner'].get('vat') == 'DE123456789':
            res['partner'].pop('vat')
            if not res['partner'].get('email'):
                res['partner']['name'] = 'Lieferant GmbH'
        logger.info('Result of Factur-X XML parsing: %s', res)
        return res
