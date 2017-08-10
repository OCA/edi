# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _inherit = 'account.invoice.import'

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
            taxes.append({
                'amount_type': 'percent',
                'amount': percentage,
                'unece_type_code': type_code,
                'unece_categ_code': categ_code,
                })
        return taxes

    def parse_facturx_invoice_line(
            self, iline, total_line_lines, global_taxes, namespaces):
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
        total_line_lines += price_subtotal
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
            'taxes': taxes or global_taxes,
            })
        return vals

    @api.model
    def parse_facturx_invoice(self, xml_root):
        """Parse Cross Industry Invoice XML file"""
        logger.debug('Starting to parse XML file as Factur-X/ZUGFeRD file')
        namespaces = xml_root.nsmap
        prec = self.env['decimal.precision'].precision_get('Account')
        logger.debug('XML file namespaces=%s', namespaces)
        doc_type = self.multi_xpath_helper(
            xml_root,
            ['//rsm:ExchangedDocument/ram:TypeCode',  # Factur-X
             '//rsm:HeaderExchangedDocument/ram:TypeCode',  # ZUGFeRD
             ], namespaces)
        # TODO add full support for 381
        sign = 1
        if doc_type not in ('380', '381'):
            raise UserError(_(
                "The Factur-X XML file is not an invoice/refund file "
                "(TypeCode is %s") % doc_type)
        elif doc_type == '381':
            sign = -1

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
        amount_total = res['amount_total']
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
        global_taxes_xpath = xml_root.xpath(
            "//ram:ApplicableSupplyChainTradeSettlement"
            "/ram:ApplicableTradeTax", namespaces=namespaces)
        global_taxes = self.parse_facturx_taxes(
            global_taxes_xpath, namespaces)
        logger.debug('global_taxes=%s', global_taxes)
        res_lines = []
        total_line_lines = 0.0
        inv_line_xpath = self.raw_multi_xpath_helper(
            xml_root, ["//ram:IncludedSupplyChainTradeLineItem"], namespaces)
        for iline in inv_line_xpath:
            line_vals = self.parse_facturx_invoice_line(
                iline, total_line_lines, global_taxes, namespaces)
            if line_vals is False:
                continue
            res_lines.append(line_vals)

        if float_compare(
                total_line, total_line_lines, precision_digits=prec):
            logger.warning(
                "The global LineTotalAmount (%s) doesn't match the "
                "sum of the LineTotalAmount of each line (%s). It can "
                "have a diff of a few cents due to sum of rounded values vs "
                "rounded sum policies.", total_line, total_line_lines)

        charge_line_xpath = self.raw_multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedLogisticsServiceCharge",  # ZUGFeRD
             ], namespaces)
        # These LogisticsServiceCharge lines don't seem to exist in Factur-X
        total_charge_lines = 0.0
        for chline in charge_line_xpath:
            name = self.multi_xpath_helper(
                chline, ["ram:Description"], namespaces)\
                or _("Logistics Service")
            price_unit = self.multi_xpath_helper(
                chline, ["ram:AppliedAmount"], namespaces, isfloat=True)
            total_charge_lines += price_unit
            taxes_xpath = self.raw_multi_xpath_helper(
                chline, ["ram:AppliedTradeTax"], namespaces)
            taxes = self.parse_facturx_taxes(taxes_xpath, namespaces)
            vals = {
                'name': name,
                'qty': 1,
                'price_unit': price_unit,
                'taxes': taxes or global_taxes,
                }
            res_lines.append(vals)

        if float_compare(
                total_charge, total_charge_lines, precision_digits=prec):
            if len(global_taxes) <= 1 and not total_charge_lines:
                res_lines.append({
                    'name': _("Logistics Service"),
                    'qty': 1,
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
                    % (total_charge, total_charge_lines))

        if float_compare(total_tradeallowance, 0, precision_digits=prec) == -1:
            tradeallowance_qty = 1
        else:
            tradeallowance_qty = -1
        tradeallowance_line_xpath = self.raw_multi_xpath_helper(
            xml_root,
            ["//ram:ApplicableHeaderTradeSettlement"
             "/ram:SpecifiedTradeAllowanceCharge",  # Factur-X
             "//ram:ApplicableSupplyChainTradeSettlement"
             "/ram:SpecifiedTradeAllowanceCharge",  # ZUGFeRD
             ], namespaces)
        total_tradeallowance_lines = 0.0
        for alline in tradeallowance_line_xpath:
            name_xpath = alline.xpath(
                "ram:Reason", namespaces=namespaces)
            name = name_xpath and name_xpath[0].text or _("Trade Allowance")
            price_unit_xpath = alline.xpath(
                "ram:ActualAmount", namespaces=namespaces)
            price_unit = abs(float(price_unit_xpath[0].text))
            total_tradeallowance_lines += price_unit
            taxes_xpath = alline.xpath(
                "ram:CategoryTradeTax", namespaces=namespaces)
            taxes = self.parse_facturx_taxes(taxes_xpath, namespaces)
            vals = {
                'name': name,
                'qty': tradeallowance_qty,
                'price_unit': price_unit,
                'taxes': taxes or global_taxes,
                }
            res_lines.append(vals)
        if float_compare(
                abs(total_tradeallowance), total_tradeallowance_lines,
                precision_digits=prec):
            if len(global_taxes) <= 1 and not total_tradeallowance_lines:
                res_lines.append({
                    'name': _("Trade Allowance"),
                    'qty': tradeallowance_qty,
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
                    % (abs(total_tradeallowance), total_tradeallowance_lines))

        res.update({
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
