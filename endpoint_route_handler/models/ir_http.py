# Copyright 2021 Camptcamp SA
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
    def _generate_routing_rules(cls, modules, converters):
        # Override to inject custom endpoint rules.
        return chain(
            super()._generate_routing_rules(modules, converters),
            cls._endpoint_routing_rules(),
        )

    @classmethod
    def _endpoint_routing_rules(cls):
        """Yield custom endpoint rules"""
        cr = http.request.env.cr
        e_registry = EndpointRegistry.registry_for(cr.dbname)
        for endpoint_rule in e_registry.get_rules():
            _logger.debug("LOADING %s", endpoint_rule)
            endpoint = endpoint_rule.endpoint
            for url in endpoint_rule.routing["routes"]:
                yield (url, endpoint, endpoint_rule.routing)

    @classmethod
    def routing_map(cls, key=None):
        cr = http.request.env.cr
        e_registry = EndpointRegistry.registry_for(cr.dbname)

        # Each `env` will have its own `ir.http` "class instance"
        # thus, each instance will have its own routing map.
        # Hence, we must keep track of which instances have been updated
        # to make sure routing rules are always up to date across envs.
        #
        # In the original `routing_map` method it's reported in a comment
        # that the routing map should be unique instead of being duplicated
        # across envs... well, this is how it works today so we have to deal w/ it.
        http_id = cls._endpoint_make_http_id()

        is_routing_map_new = not hasattr(cls, "_routing_map")
        if is_routing_map_new or not e_registry.ir_http_seen(http_id):
            # When the routing map is not ready yet, simply track current instance
            e_registry.ir_http_track(http_id)
            _logger.debug("ir_http instance `%s` tracked", http_id)
        elif e_registry.ir_http_seen(http_id) and e_registry.routing_update_required(
            http_id
        ):
            # This instance was already tracked
            # and meanwhile the registry got updated:
            # ensure all routes are re-loaded.
            _logger.info(
                "Endpoint registry updated, reset routing ma for `%s`", http_id
            )
            cls._routing_map = {}
            cls._rewrite_len = {}
            e_registry.reset_update_required(http_id)
        return super().routing_map(key=key)

    @classmethod
    def _endpoint_make_http_id(cls):
        """Generate current ir.http class ID."""
        return id(cls)

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
