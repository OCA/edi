# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_shipping_partner(self, shipping_dict, partner, chatter_msg):
        partner_obj = self.env['res.partner']

        if 'partner' in shipping_dict\
                and shipping_dict['partner'].get('edifact_code', False):
            edifact_code = shipping_dict['partner']['edifact_code']
            delivery = False
            if shipping_dict['partner'].get(
                    'edifact_type', False) == 'delivery':
                delivery = True
            res = partner_obj.find_partner_by_edifact_code(
                edifact_code, partner.id, delivery=delivery)
        else:
            res = super(BusinessDocumentImport, self)._match_shipping_partner(
                shipping_dict, partner, chatter_msg)
        return res

    @api.model
    def _match_partner(
            self, partner_dict, chatter_msg, partner_type='supplier'):
        partner_obj = self.env['res.partner']

        if 'edifact_code' in partner_dict:
            parent_id = self._context.get('edifact_partner_parent_id', False)
            partner = partner_obj.find_partner_by_edifact_code(
                partner_dict['edifact_code'], parent_id)
            if not partner:
                raise self.user_error_wrap(_(
                    'Odoo couldn\'t find any partner with Edifact code: %s')
                    % partner_dict['edifact_code'])
        else:
            partner = super(BusinessDocumentImport, self)._match_partner(
                partner_dict, chatter_msg, partner_type=partner_type)

        return partner
