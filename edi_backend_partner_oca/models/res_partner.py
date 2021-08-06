# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    edi_backend_ids = fields.One2many(
        comodel_name="edi.backend", inverse_name="partner_id",
    )
    edi_backend_count = fields.Integer(compute="_compute_edi_backend_count")

    def _compute_edi_backend_count(self):
        for rec in self:
            rec.edi_backend_count = len(rec.edi_backend_ids)

    def action_edi_backend(self):
        action = self.env.ref("edi.act_open_edi_backend_view")
        result = action.read()[0]
        backends = self.mapped("edi_backend_ids")
        if len(backends) > 1:
            result["domain"] = [("id", "in", backends.ids)]
        else:
            res = self.env.ref("edi.edi_backend_view_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = backends.id
        return result
