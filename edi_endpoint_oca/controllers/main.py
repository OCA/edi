# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import http

from odoo.addons.endpoint.controllers.main import EndpointControllerMixin


class EDIEndpointController(http.Controller, EndpointControllerMixin):
    def _find_endpoint(self, env, endpoint_route):
        return env["edi.endpoint"]._find_endpoint(endpoint_route)
