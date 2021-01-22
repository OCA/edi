# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from datetime import datetime
from slugify import slugify


class BaseEdifact(models.AbstractModel):
    _name = 'base.edifact'
    _description =\
        'Common methods to generate and parse Edifact plain text files'

    def get_vat(self, partner):
        vat = ''
        if partner.vat:
            vat = partner._split_vat(partner.vat)[1]
        return vat

    def get_partner_data(self, partner):
        name = slugify(partner.name, separator=' ', lowercase=False,
                       max_length=70)
        city = slugify(partner.name, separator=' ', lowercase=False,
                       max_length=35)
        street = partner.street or ''
        if partner.street2:
            if street:
                street += ' '
            street += partner.street2
        # Only ASCII chars:
        street = slugify(street, separator=' ', lowercase=False, max_length=70)
        return (name, city, street)

    @api.model
    def edifact_date(self, date):
        return '%s%s%s' % (date.year,
                           '{0:02d}'.format(date.month),
                           '{0:02d}'.format(date.day))

    # Methods to generate: invoice
    @api.model
    def edifact_invoice_init(self):
        return 'INVOIC_D_93A_UN_EAN007\n'

    @api.model
    def edifact_invoice_name(self, invoice_number, invoice_type):
        if invoice_type == 'out_invoice':
            invoice_type = '380'
        else:
            invoice_type = '381'
        return 'INV|%s|%s|9\n' % (invoice_number, invoice_type)

    @api.model
    def edifact_invoice_date(self, invoice_date):
        invoice_date_str = self.edifact_date(invoice_date)
        return 'DTM|%s\n' % invoice_date_str

    @api.model
    def edifact_invoice_references(self, ref_type, item_number, item_date):
        ref_code = False
        if ref_type == 'picking':
            ref_code = 'DQ'
        else:
            ref_code = 'ON'
        date_str = self.edifact_date(item_date)
        return 'RFF|%s|%s|%s\n' % (ref_code, item_number, date_str)

    @api.model
    def edifact_invoice_buyer(self, partner):
        name, city, street = self.get_partner_data(partner)
        vat = self.get_vat(partner)
        return 'NADBY|%s|%s|%s|%s|%s|%s||%s\n' % (
            partner.edifact_code or '',
            name or '',
            street,
            city or '',
            partner.zip or '',
            vat,
            partner.country_id.code or ''
        )

    @api.model
    def edifact_invoice_receiver(self, partner):
        name, city, street = self.get_partner_data(partner)
        vat = self.get_vat(partner)
        return 'NADIV|%s|%s|%s|%s|%s|%s\n' % (
            partner.edifact_code or '',
            name or '',
            street,
            city or '',
            partner.zip or '',
            vat,
        )

    @api.model
    def edifact_invoice_legal_buyer(self, partner):
        name, city, street = self.get_partner_data(partner)
        vat = self.get_vat(partner)
        res = 'NADBCO|%s|%s|%s|%s|%s|%s' % (
            partner.edifact_code or '',
            name or '',
            street,
            city or '',
            partner.zip or '',
            vat,
        )
        if partner.country_id:
            res += '|%s' % partner.country_id.code
        res += '\n'
        return res

    @api.model
    def edifact_invoice_supplier(self, supplier, company_registry):
        name, city, street = self.get_partner_data(supplier)
        vat = self.get_vat(supplier)
        return 'NADSU|%s|%s|%s|%s|%s|%s|%s\n' % (
            supplier.edifact_code or '',
            name or '',
            company_registry or '',
            street,
            city or '',
            supplier.zip or '',
            vat,
        )

    @api.model
    def edifact_invoice_legal_supplier(self, supplier, company_registry):
        name, city, street = self.get_partner_data(supplier)
        vat = self.get_vat(supplier)
        return 'NADSCO|%s|%s|%s|%s|%s|%s|%s\n' % (
            supplier.edifact_code or '',
            name or '',
            company_registry or '',
            street,
            city or '',
            supplier.zip or '',
            vat,
        )

    @api.model
    def edifact_invoice_goods_receiver(self, partner):
        name, city, street = self.get_partner_data(partner)
        return 'NADDP|%s|%s|%s|%s|%s\n' % (
            partner.edifact_code or '',
            name or '',
            street,
            city or '',
            partner.zip or '',
        )

    @api.model
    def edifact_invoice_payer(self, partner):
        return 'NADPR|%s\n' % partner.edifact_code

    @api.model
    def edifact_invoice_currency(self, currency):
        return 'CUX|%s|4\n' % currency.name

    @api.model
    def edifact_invoice_optional_fields(self, invoice):
        # Method to be inherit by personalizations and add required stuff
        return ''

    # Methods to generate: invoice line
    @api.model
    def edifact_invoice_line_init(self, invoice_line, index):
        return 'LIN|%s|EN|%s\n' % (invoice_line.product_id.barcode, index+1)

    @api.model
    def edifact_invoice_line_description(self, invoice_line):
        # Description Max length: 70
        description = slugify(invoice_line.product_id.name, separator=' ',
                              lowercase=False, max_length=70)
        return 'IMDLIN|%s|M|F\n' % description

    @api.model
    def edifact_invoice_line_quantity(self, invoice_line):
        if invoice_line.uom_id.id == self.env.ref('uom.product_uom_unit').id:
            uom_code = 'PCE'
        elif invoice_line.uom_id.id == self.env.ref('uom.product_uom_kgm').id:
            uom_code = 'KGM'
        elif invoice_line.uom_id.id ==\
                self.env.ref('uom.product_uom_litre').id:
            uom_code = 'LTR'
        elif invoice_line.uom_id.id == self.env.ref('uom.product_uom_ton').id:
            uom_code = 'TNE'
        elif invoice_line.uom_id.id ==\
                self.env.ref('uom.product_uom_meter').id:
            uom_code = 'MTR'
        else:
            uom_code = 'PCE'
        res = 'QTYLIN|46|%s|%s\n\
QTYLIN|47|%s|%s\n' % (int(invoice_line.quantity), uom_code,
                      int(invoice_line.quantity), uom_code,)
        return res

    @api.model
    def edifact_invoice_line_price_unit(self, invoice_line):
        discounted_price = invoice_line.price_unit - (
            invoice_line.price_unit * invoice_line.discount / 100.0)
        res = 'PRILIN|AAA|%.2f\n\
PRILIN|AAB|%.2f\n' % (discounted_price, invoice_line.price_unit)
        return res

    @api.model
    def edifact_invoice_line_discount(self, invoice_line):
        res = ''
        if invoice_line.discount:
            discount_amount = round(
                invoice_line.price_unit * invoice_line.quantity * (
                    invoice_line.discount or 0.0) / 100.0, 2)
            res = 'ALCLIN|A|1|TD||%s|%s\n' % (
                invoice_line.discount, discount_amount)
        return res

    @api.model
    def edifact_invoice_line_taxes(self, tax_code, tax_percent, tax_amount):
        return 'TAXLIN|%s|%s|%.2f\n' % (tax_code, tax_percent, tax_amount)

    @api.model
    def edifact_invoice_line_total(self, invoice_line):
        return 'MOALIN|%s\n' % invoice_line.price_subtotal

    @api.model
    def edifact_invoice_detail_lines(self):
        return 'CNTRES|2\n'

    @api.model
    def edifact_invoice_amount_total(
            self, untaxed_amount, total_amount, total_tax_amount,
            without_discounts, with_discounts, discounts_amount):
        res = 'MOARES|%.2f|%.2f|%.2f|%s|%.2f' % (
            with_discounts,
            without_discounts,
            untaxed_amount,
            total_amount,
            total_tax_amount,
        )
        if discounts_amount:
            res += '|%.2f' % discounts_amount
        res += '\n'
        return res

    @api.model
    def edifact_invoice_result_taxes(
            self, tax_code, tax_percent, tax_amount, untaxed_amount):
        return 'TAXRES|%s|%s|%.2f|%.2f\n' % (
            tax_code, tax_percent, tax_amount, untaxed_amount)

    # Methods to parse: Sale Order
    @api.model
    def edifact_parse_order_ref(self, order_segments):
        if order_segments[0] != 'ORD':
            return False
        return order_segments[1]

    @api.model
    def edifact_parse_partner(self, partner_segments):
        if partner_segments[0] != 'NADBY':
            return False

        partner_dict = {
            'edifact_code': partner_segments[1],
            'name': len(partner_segments) > 5 and partner_segments[5],
            'street': len(partner_segments) > 6 and partner_segments[6],
            'city': len(partner_segments) > 7 and partner_segments[7],
            'zip': len(partner_segments) > 8 and partner_segments[8] or False,
            'vat':
                len(partner_segments) > 9 and partner_segments[9] or False,
        }
        return partner_dict

    @api.model
    def edifact_parse_address(self, address_segments):
        if address_segments[0] not in ('NADDP', 'NADIV'):
            return False
        elif address_segments[0] == 'NADDP':
            type = 'delivery'
        else:
            type = 'invoice'

        # When dealing edifact address only check edifact_code:
        address_dict = {
            'partner': {
                'edifact_code': address_segments[1],
                'edifact_type': type,
                'name': False,
                'email': False,
                'vat': False,
            },
            'address': {
                'street': False,
                'city': False,
                'zip': False,
            }
        }

        return address_dict

    @api.model
    def edifact_parse_date(self, date_segments):
        if len(date_segments) < 2 or date_segments[0] != 'DTM':
            return False
        if date_segments[1]:
            res = datetime.strptime(date_segments[1], '%Y%m%d')
        else:
            res = False
        return res

    @api.model
    def edifact_parse_commitment_date(self, date_segments):
        if len(date_segments) < 3 or date_segments[0] != 'DTM':
            return False
        if date_segments[2]:
            res = datetime.strptime(date_segments[2], '%Y%m%d')
        else:
            res = False
        return res

    @api.model
    def edifact_parse_currency(self, currency_segments):
        if currency_segments[0] != 'CUX':
            return False
        currency = {
            'iso': currency_segments[1],
            'symbol': False,
        }
        if currency['iso'] == 'EUR':
            currency['symbol'] = '€'
        elif currency['iso'] == 'USD':
            currency['symbol'] = '$'
        return currency

    @api.model
    def edifact_parse_product(self, product_segments):
        if product_segments[0] != 'LIN':
            return False
        product = {
            'code': False,
            'barcode': False,
        }
        if product_segments[2] == 'EN':
            product['barcode'] = product_segments[1]
        elif product_segments[2] == 'UP':
            product['code'] = product_segments[1]
        return product

    @api.model
    def edifact_parse_quantity(self, qty_segments, line):
        if qty_segments[0] != 'QTYLIN':
            return False
        if qty_segments[1] == '21':
            line['qty'] = int(qty_segments[2])
        return True

    @api.model
    def edifact_parse_price_unit(self, price_segments, line):
        if price_segments[0] != 'PRILIN':
            return False
        if price_segments[1] == 'AAA':
            # Price without taxes:
            line['price_unit'] = float(price_segments[2])
        return True
