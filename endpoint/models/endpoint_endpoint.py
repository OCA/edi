from odoo import models


class EndpointEndpoint(models.Model):
    """Define a custom endpoint."""

    _name = "endpoint.endpoint"
    _inherit = "endpoint.mixin"
    _description = "Endpoint"
