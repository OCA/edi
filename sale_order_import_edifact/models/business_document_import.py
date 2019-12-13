# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_partner(
            self, partner_dict, chatter_msg, partner_type='supplier'):
        rpo = self.env['res.partner']

        if 'edifact_code' in partner_dict:
            company_id = self._context.get('force_company') or\
                self.env.user.company_id.id
            domain = [
                '|', ('company_id', '=', False),
                ('company_id', '=', company_id),
                ('edifact_code', '=', partner_dict['edifact_code']),
                ('type', 'not in', ('delivery', 'invoice'))]
            partner = rpo.search(domain, limit=1)
            if partner:
                return partner
        partner = super(BusinessDocumentImport, self)._match_partner(
            partner_dict, chatter_msg, partner_type=partner_type)

        return partner
