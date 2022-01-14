# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


# TODO add view
class EDIBackendType(models.Model):

    _inherit = "edi.backend.type"

    endpoint_ids = fields.One2many(
        string="Endpoints",
        comodel_name="edi.endpoint",
        inverse_name="backend_type_id",
    )
