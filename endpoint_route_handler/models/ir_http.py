# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

import werkzeug

from odoo import http, models

from ..registry import EndpointRegistry

_logger = logging.getLogger(__name__)


def safely_add_rule(rmap, rule):
    """Add rule to given route map without breaking."""
    if rule.endpoint not in rmap._rules_by_endpoint:
        # When the rmap gets re-generated, unbound the old one.
        if rule.map:
            rule.bind(rmap, rebind=True)
        else:
            rmap.add(rule)
        _logger.info("LOADED %s", str(rule))


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def routing_map(cls, key=None):
        # Override to inject custom endpoint routes
        rmap = super().routing_map(key=key)
        if hasattr(cls, "_routing_map"):
            cr = http.request.env.cr
            endpoint_registry = EndpointRegistry.registry_for(cr.dbname)
            if not hasattr(cls, "_endpoint_routing_map_loaded"):
                # First load, register all endpoint routes
                cls._load_endpoint_routing_map(rmap, endpoint_registry)
                cls._endpoint_routing_map_loaded = True
            elif endpoint_registry.routing_update_required():
                # Some endpoint changed, we must reload
                cls._reload_endpoint_routing_map(rmap, endpoint_registry)
                endpoint_registry.reset_update_required()
        return rmap

    @classmethod
    def _clear_routing_map(cls):
        super()._clear_routing_map()
        if hasattr(cls, "_endpoint_routing_map_loaded"):
            delattr(cls, "_endpoint_routing_map_loaded")

    @classmethod
    def _load_endpoint_routing_map(cls, rmap, endpoint_registry):
        for rule in endpoint_registry.get_rules():
            safely_add_rule(rmap, rule)
        _logger.info("Endpoint routing map loaded")
        # If you have to debug, ncomment to print all routes
        # print("\n".join([x.rule for x in rmap._rules]))

    @classmethod
    def _reload_endpoint_routing_map(cls, rmap, endpoint_registry):
        """Reload endpoints routing map.

        Take care of removing obsolete ones and add new ones.
        The match is done using the `_endpoint_hash`.

        Typical log entries in case of route changes:

        [...] endpoint.endpoint: Registered controller /demo/one/new (auth: public)
        [...] odoo.addons.endpoint.models.ir_http: DROPPED /demo/one
        [...] odoo.addons.endpoint.models.ir_http: LOADED /demo/one/new
        [...] odoo.addons.endpoint.models.ir_http: Endpoint routing map re-loaded

        and then on subsequent calls:

        [...] GET /demo/one HTTP/1.1" 404 - 3 0.001 0.006
        [...] GET /demo/one/new HTTP/1.1" 200 - 6 0.001 0.005

        You can look for such entries in logs
        to check visually that a route has been updated
        """
        to_update = endpoint_registry.get_rules_to_update()
        to_load = to_update["to_load"]
        to_drop = to_update["to_drop"]
        hashes_to_drop = [x._endpoint_hash for x in to_drop]
        remove_count = 0
        for i, rule in enumerate(rmap._rules[:]):
            if (
                hasattr(rule, "_endpoint_hash")
                and rule._endpoint_hash in hashes_to_drop
            ):
                if rule.endpoint in rmap._rules_by_endpoint:
                    rmap._rules.pop(i - remove_count)
                    rmap._rules_by_endpoint.pop(rule.endpoint)
                    remove_count += 1
                    _logger.info("DROPPED %s", str(rule))
                    continue
        for rule in to_load:
            safely_add_rule(rmap, rule)
        _logger.info("Endpoint routing map re-loaded")

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
