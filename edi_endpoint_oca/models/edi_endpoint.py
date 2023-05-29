# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import werkzeug

from odoo import _, api, exceptions, fields, models
from odoo.tools import safe_eval


class EDIEndpoint(models.Model):
    """EDI endpoint.

    Manage endpoints used within EDI framework.
    """

    _name = "edi.endpoint"
    _inherit = ["endpoint.mixin"]
    _description = "EDI Endpoint"

    _endpoint_route_prefix = "/edi"

    backend_type_id = fields.Many2one(
        comodel_name="edi.backend.type",
        required=True,
    )
    # Leave these as not required to allow pre-configuration of endpoints by backend type
    backend_id = fields.Many2one(
        comodel_name="edi.backend", domain="[('backend_type_id','=', backend_type_id)]"
    )
    exchange_type_id = fields.Many2one(
        comodel_name="edi.exchange.type",
        domain="[('backend_type_id','=', backend_type_id)]",
    )

    # TODO: add unit tests

    def create_exchange_record(self, file_content=None, **vals):
        """Create an EDI exchange record from current endpoint.

        Just a shortcut.
        """
        self._check_endpoint_ready()
        vals["edi_endpoint_id"] = self.id
        rec = self.backend_id.create_record(self.exchange_type_id.code, vals)
        if file_content:
            rec._set_file_content(file_content)
        return rec

    def _check_endpoint_ready(self, request=False):
        if not self.backend_id or not self.exchange_type_id:
            msg = _("Backend and exchange type are mandatory")
            if request:
                self._logger.error(msg)
                raise werkzeug.exceptions.BadRequest("Endpoint mis-configured")
            else:
                raise exceptions.UserError(msg)

    @api.constrains("exchange_type_id", "backend_type_id")
    def _check_backend_type(self):
        for rec in self:
            if (
                rec.backend_type_id
                and rec.exchange_type_id
                and not rec.backend_type_id == rec.exchange_type_id.backend_type_id
            ):
                raise exceptions.UserError(
                    _("Exchange type not compatible with selected backend type.")
                )

    def _handle_request(self, request):
        self._check_endpoint_ready(request=True)
        return super()._handle_request(request)

    def action_view_edi_records(self):
        self.ensure_one()
        xmlid = "edi_oca.act_open_edi_exchange_record_view"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("edi_endpoint_id", "=", self.id)]
        # Purge default search filters from ctx to avoid hiding records
        ctx = action.get("context", {})
        if isinstance(ctx, str):
            ctx = safe_eval.safe_eval(ctx, self.env.context)
        action["context"] = {
            k: v for k, v in ctx.items() if not k.startswith("search_default_")
        }
        # Drop ID otherwise the context will be loaded from the action's record :S
        action.pop("id")
        return action
