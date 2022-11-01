# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from itertools import chain

import werkzeug

from odoo import http, models

from ..registry import EndpointRegistry

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _endpoint_route_registry(cls, env):
        return EndpointRegistry.registry_for(env.cr)

    @classmethod
    def _generate_routing_rules(cls, modules, converters):
        # Override to inject custom endpoint rules.
        return chain(
            super()._generate_routing_rules(modules, converters),
            cls._endpoint_routing_rules(),
        )

    @classmethod
    def _endpoint_routing_rules(cls):
        """Yield custom endpoint rules"""
        e_registry = cls._endpoint_route_registry(http.request.env)
        for endpoint_rule in e_registry.get_rules():
            _logger.debug("LOADING %s", endpoint_rule)
            endpoint = endpoint_rule.endpoint
            for url in endpoint_rule.routing["routes"]:
                yield (url, endpoint, endpoint_rule.routing)

    @classmethod
    def routing_map(cls, key=None):
        last_update = cls._get_routing_map_last_update(http.request.env)
        if not hasattr(cls, "_routing_map"):
            # routing map just initialized, store last update for this env
            cls._endpoint_route_last_update = last_update
        elif cls._endpoint_route_last_update < last_update:
            _logger.info("Endpoint registry updated, reset routing map")
            cls._routing_map = {}
            cls._rewrite_len = {}
            cls._endpoint_route_last_update = last_update
        return super().routing_map(key=key)

    @classmethod
    def _get_routing_map_last_update(cls, env):
        return cls._endpoint_route_registry(env).last_update()

    @classmethod
    def _clear_routing_map(cls):
        super()._clear_routing_map()
        if hasattr(cls, "_endpoint_route_last_update"):
            cls._endpoint_route_last_update = 0

    @classmethod
    def _auth_method_user_endpoint(cls):
        """Special method for user auth which raises Unauthorized when needed.

        If you get an HTTP request (instead of a JSON one),
        the standard `user` method raises `SessionExpiredException`
        when there's no user session.
        This leads to a redirect to `/web/login`
        which is not desiderable for technical endpoints.

        This method makes sure that no matter the type of request we get,
        a proper exception is raised.
        """
        try:
            cls._auth_method_user()
        except http.SessionExpiredException:
            raise werkzeug.exceptions.Unauthorized()
