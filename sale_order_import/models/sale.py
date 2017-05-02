# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def name_get(self):
        """Add amount_untaxed in name_get of sale orders"""
        res = super(SaleOrder, self).name_get()
        if self._context.get('sale_order_show_amount'):
            new_res = []
            for (sale_id, name) in res:
                sale = self.browse(sale_id)
                # I didn't find a python method to easily display
                # a float + currency symbol (before or after)
                # depending on lang of context and currency
                name += _(' Amount w/o tax: %s %s)') % (
                    sale.amount_untaxed, sale.currency_id.name)
                new_res.append((sale_id, name))
            return new_res
        else:
            return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner(self,  part):
        if not part:
            return {'value': {'partner_invoice_id': False,
                              'partner_shipping_id': False,
                              'payment_term': False,
                              'fiscal_position': False
                              }

                    }

        addr = self.partner_id.address_get(['delivery', 'invoice', 'contact'])

        pricelist = self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,

        payment_term = self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
        dedicated_salesman = self.partner_id.user_id.id
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }

        if pricelist:
            val['pricelist_id'] = pricelist

        if self.env.user.company_id.sale_note:
            val['note'] = self.with_context(
                lang=self.partner_id.lang).env.user.company_id.sale_note

        return {'value': val}