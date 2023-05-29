# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EDIExchangeRecord(models.Model):

    _inherit = "edi.exchange.record"

    edi_endpoint_id = fields.Many2one(
        comodel_name="edi.endpoint",
        readonly=True,
        string="Endpoint",
        help="Record generated via this endpoint",
    )
