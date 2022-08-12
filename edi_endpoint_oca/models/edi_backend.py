# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, exceptions, fields, models


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
        xmlid = "edi_endpoint_oca.edi_endpoint_act_window"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [
            ("backend_type_id", "=", self.backend_type_id.id),
            "|",
            ("backend_id", "=", False),
            ("backend_id", "=", self.id),
        ]
        action["context"] = {
            "default_backend_id": self.id,
            "default_backend_type_id": self.backend_type_id.id,
        }
        return action

    @api.constrains("active")
    def _check_archive(self):
        to_check = [
            x
            for x in self
            if not x.active and x.endpoint_ids.filtered(lambda x: x.active)
        ]
        if to_check:
            raise exceptions.UserError(self._check_archive_error_msg(to_check))

    def _check_archive_error_msg(self, backends):
        return _(
            "The following backend(s) have endpoints attached. "
            "Please archive them before:\n\n%s"
        ) % "\n- ".join([x.name for x in backends])
