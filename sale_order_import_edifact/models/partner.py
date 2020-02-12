# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edifact_code = fields.Char(string='Edifact Code')

    def find_partner_by_edifact_code(
            self, edifact_code, parent_id, delivery=False):
        company_id = self._context.get('force_company') or\
            self.env.user.company_id.id
        domain = [
            '|', ('company_id', '=', False),
            ('company_id', '=', company_id),
            ('edifact_code', '=', edifact_code),
        ]
        if not delivery:
            domain.append(('type', '!=', 'delivery'))
        partners = self.search(domain)
        partner = False
        if len(partners) > 1 and parent_id:
            domain.append(('parent_id', '=', parent_id))
            partners = self.search([
                ('id', 'in', partners.ids),
                ('parent_id', '=', parent_id)], limit=1)
        if len(partners) == 1:
            partner = partners[0]
        elif len(partners) > 1:
            # partner = partners[0]
            raise UserError(
                _('Multiple partner sharing edifact code: %s') % edifact_code)
        return partner
