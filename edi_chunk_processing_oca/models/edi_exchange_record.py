# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    chunk_group_id = fields.Many2one("chunk.group", string="Chunk Group")

    _sql_constraints = [
        ("uniq_chunk_group_id", "unique(chunk_group_id)", "The Group must be unique!")
    ]
