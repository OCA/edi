# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class EDIBackend(models.Model):

    _inherit = "edi.backend"

    endpoint_ids = fields.One2many(
        string="Endpoints",
        comodel_name="edi.endpoint",
        inverse_name="backend_id",
    )
    endpoints_count = fields.Integer(compute="_compute_endpoints_count")

    @api.depends("endpoint_ids")
    def _compute_endpoints_count(self):
        for record in self:
            record.endpoints_count = len(record.endpoint_ids)

    def action_manage_endpoints(self):
        action = self.env.ref("edi_endpoint_oca.edi_endpoint_act_window").read()[0]
        action["domain"] = [
            ("backend_type_id", "=", self.backend_type_id),
            "|",
            ("backend_id", "=", False),
            ("backend_id", "=", self.id),
        ]
        action["context"] = {
            "default_backend_id": self.id,
            "default_backend_type_id": self.backend_type_id.id,
        }
        return action
