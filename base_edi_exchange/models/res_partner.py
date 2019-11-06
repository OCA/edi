# -*- coding: utf-8 -*-
# Copyright 2019 Callino <wpichler@callino.at
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('available_exchange_ids')
    def _get_edi_exchange_available(self):
        for record in self:
            record.edi_exchange_available = True if record.available_exchange_ids else False

    available_exchange_ids = fields.Many2many(
        comodel_name="base.edi.exchange",
        relation="partner_exchange_rel",
        column_1="partner_id",
        column_2="exchange_id",
        string="Available Exchanges"
    )
    edi_exchange_available = fields.Boolean(string="EDI Exchange Available",
                                            compute=_get_edi_exchange_available,
                                            store=True)


# Relation Model with Sequence to have an easily adjustable order
class PartnerExchangeRel(models.Model):
    _name = 'partner.exchange.rel'
    _order = 'sequence asc'

    sequence = fields.Integer(string="Sequence", default=10)
    partner_id = fields.Many2one('res.partner', string="Partner")
    exchange_id = fields.Many2one('base.edi.exchange', string="Exchange")
