# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from datetime import datetime


class BaseEdifact(models.AbstractModel):
    _name = 'base.edifact'
    _description =\
        'Common methods to generate and parse Edifact plain text files'

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
            'name': partner_segments[5],
            'street': partner_segments[6],
            'city': partner_segments[7],
            'zip': len(partner_segments) >= 9 and partner_segments[8] or False,
            'vat':
                len(partner_segments) >= 10 and partner_segments[9] or False,
        }
        return partner_dict

    @api.model
    def edifact_parse_address(self, address_segments):
        if address_segments[0] not in ('NADDP', 'NADIV'):
            return False

        address_dict = {
            'partner': {
                'name': address_segments[3] or False,
                'email': False,
            },
            'address': {
                'street': address_segments[4] or False,
                'city': address_segments[5] or False,
                'zip': address_segments[6] or False,
            }
        }
        if len(address_segments) >= 8:
            address_dict['vat'] = address_segments[7] or False
        return address_dict

    @api.model
    def edifact_parse_date(self, date_segments):
        if date_segments[0] != 'DTM':
            return False
        if date_segments[1]:
            res = datetime.strptime(date_segments[1], '%Y%m%d')
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
