# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import datetime
import logging
from lxml import etree
import mimetypes

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
logger = logging.getLogger(__name__)

try:
    import xmlsig
except(ImportError, IOError) as err:
    logging.info(err)

facturae_ns = 'http://www.facturae.es/Facturae/2009/v3.2/Facturae'


class AccountInvoiceImport(models.TransientModel):
    _inherit = 'account.invoice.import'

    @api.multi
    def parse_invoice(self):
        mimetypes.add_type('application/xml', '.xsig')
        return super().parse_invoice()

    @api.model
    def parse_xml_invoice(self, xml_root):
        if (
            xml_root.tag and
            xml_root.tag.startswith('{%s}Facturae' % facturae_ns)
        ):
            return self.parse_facturae_invoice(xml_root)
        return super().parse_xml_invoice(xml_root)

    @api.model
    def parse_facturae_invoice(self, xml_root):
        facturae_schema = etree.XMLSchema(
            etree.parse(tools.file_open(
                "Facturaev3_2.xsd",
                subdir="addons/account_invoice_import_facturae/data"
            )))
        facturae_schema.assertValid(xml_root)
        sign = xml_root.find(
            'ds:Signature', namespaces={'ds': xmlsig.constants.DSigNs}
        )
        if sign is not None:
            xmlsig.SignatureContext().verify(sign)
        modality = xml_root.find('FileHeader/Modality').text
        if modality == 'L':
            raise ValidationError(_('System does not allow lots'))
        supplier_dict = self.facturae_parse_partner(xml_root, xml_root.find(
            'Parties/SellerParty'
        ))
        invoice = xml_root.find('Invoices/Invoice')

        inv_number_xpath = invoice.find('InvoiceHeader/InvoiceNumber')
        inv_type = 'in_invoice'
        inv_class = invoice.find('InvoiceHeader/InvoiceClass')
        if inv_class is not None and inv_class.text not in ['OO', 'OC']:
            inv_type = 'in_refund'
        date_dt = datetime.strptime(
            invoice.find('InvoiceIssueData/IssueDate').text, '%Y-%M-%d')
        date_start = False
        date_end = False
        amount_total = float(invoice.find('InvoiceTotals/InvoiceTotal').text)
        amount_untaxed = float(invoice.find(
            'InvoiceTotals/TotalGrossAmountBeforeTaxes'
        ).text)
        res_lines = [
            self.facturae_parse_line(xml_root, invoice, line) for line in
            invoice.find('Items').findall('InvoiceLine')
        ]
        attachments = {}
        res = {
            'type': inv_type,
            'partner': supplier_dict,
            'invoice_number': inv_number_xpath.text,
            'date': fields.Date.to_string(date_dt),
            'date_due': False,
            'date_start': date_start,
            'date_end': date_end,
            'currency': {'iso': invoice.find(
                'InvoiceIssueData/InvoiceCurrencyCode').text},
            'amount_total': amount_total,
            'amount_untaxed': amount_untaxed,
            'iban': False,
            'bic': False,
            'lines': res_lines,
            'attachments': attachments,
        }
        logger.info('Result of UBL XML parsing: %s', res)
        return res

    def facturae_parse_partner(self, xml_root, partner):
        if partner.find('TaxIdentification/ResidenceTypeCode').text == 'R':
            iso = 'ESP'
        elif partner.find('TaxIdentification/PersonTypeCode').text == 'F':
            iso = partner.find('Individual/OverseasAddress/CountryCode').text
        else:
            iso = partner.find('LegalEntity/OverseasAddress/CountryCode').text
        country = self.env['res.country'].search([('code_alpha3', '=', iso)])
        country.ensure_one()
        vat = partner.find('TaxIdentification/TaxIdentificationNumber').text
        if not vat.startswith(country.code):
            vat = country.code + vat
        return {
            'vat': vat,
        }

    def facturae_tax_to_unece(self):
        return {}

    def facturae_parse_line(self, xml_root, invoice, line):
        taxes = []
        tax_map = self.facturae_tax_to_unece()
        for tax in line.findall('TaxesWithheld/Tax'):
            taxes.append({
                'amount_type': 'percent',
                'amount': -float(tax.find('TaxRate').text),
                'unece_type_code': tax_map.get(
                    tax.find('TaxTypeCode').text, False),
            })
        for tax in line.findall('TaxesOutputs/Tax'):
            taxes.append({
                'amount_type': 'percent',
                'amount': float(tax.find('TaxRate').text),
                'unece_type_code': tax_map.get(
                    tax.find('TaxTypeCode').text, False),
            })
        product_code = False
        if line.find('ArticleCode') is not None:
            product_code = line.find('ArticleCode').text
        return {
            'product': {'code': product_code},
            'name': line.find('ItemDescription').text,
            'qty': float(line.find('Quantity').text),
            'price_unit': float(line.find('UnitPriceWithoutTax').text),
            'taxes': taxes,
        }
