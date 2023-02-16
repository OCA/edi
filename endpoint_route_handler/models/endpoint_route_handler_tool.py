# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, models


class EndpointRouteHandlerTool(models.TransientModel):
    """Model meant to be used as a tool.

    From v15 on we cannot initialize AbstractModel using `new()` anymore.
    Here we proxy the abstract model with a transient model so that we can initialize it
    but we don't care at all about storing it in the DB.
    """

    # TODO: try using `_auto = False`

    _name = "endpoint.route.handler.tool"
    _inherit = "endpoint.route.handler"
    _description = "Endpoint Route handler tool"

    def _refresh_endpoint_data(self):
        """Enforce refresh of route computed fields.

        Required for NewId records when using this model as a tool.
        """
        self._compute_endpoint_hash()
        self._compute_route()

    def _register_controllers(self, init=False, options=None):
        if self:
            self._refresh_endpoint_data()
        return super()._register_controllers(init=init, options=options)

    def _unregister_controllers(self):
        if self:
            self._refresh_endpoint_data()
        return super()._unregister_controllers()

    @api.model
    def new(self, values=None, origin=None, ref=None):
        values = values or {}  # note: in core odoo they use `{}` as defaul arg :/
        res = super().new(values=values, origin=origin, ref=ref)
        res._refresh_endpoint_data()
        return res
