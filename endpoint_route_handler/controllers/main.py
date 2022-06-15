# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging

from werkzeug.exceptions import NotFound

from odoo import http

_logger = logging.getLogger(__file__)


class EndpointNotFoundController(http.Controller):
    def auto_not_found(self, endpoint_route, **params):
        _logger.error("Non registered endpoint for %s", endpoint_route)
        raise NotFound()
