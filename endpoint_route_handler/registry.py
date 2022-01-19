# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

_REGISTRY_BY_DB = {}


class EndpointRegistry:
    """Registry for endpoints.

    Used to:

    * track registered endpoints
    * track routes to be updated for specific ir.http instances
    * retrieve routing rules to load in ir.http routing map
    """

    __slots__ = ("_mapping", "_http_ids", "_http_ids_to_update")

    def __init__(self):
        # collect EndpointRule objects
        self._mapping = {}
        # collect ids of ir.http instances
        self._http_ids = set()
        # collect ids of ir.http instances that need update
        self._http_ids_to_update = set()

    def get_rules(self):
        return self._mapping.values()

    # TODO: add test
    def get_rules_by_group(self, group):
        for key, rule in self._mapping.items():
            if rule.route_group == group:
                yield (key, rule)

    def add_or_update_rule(self, rule, force=False, init=False):
        """Add or update an existing rule.

        :param rule: instance of EndpointRule
        :param force: replace a rule forcedly
        :param init: given when adding rules for the first time
        """
        key = rule.key
        existing = self._mapping.get(key)
        if not existing or force:
            self._mapping[key] = rule
            if not init:
                self._refresh_update_required()
            return True
        if existing.endpoint_hash != rule.endpoint_hash:
            # Override and set as to be updated
            self._mapping[key] = rule
            if not init:
                self._refresh_update_required()
            return True

    def drop_rule(self, key):
        existing = self._mapping.pop(key, None)
        if not existing:
            return False
        self._refresh_update_required()
        return True

    def routing_update_required(self, http_id):
        return http_id in self._http_ids_to_update

    def _refresh_update_required(self):
        for http_id in self._http_ids:
            self._http_ids_to_update.add(http_id)

    def reset_update_required(self, http_id):
        self._http_ids_to_update.discard(http_id)

    @classmethod
    def registry_for(cls, dbname):
        if dbname not in _REGISTRY_BY_DB:
            _REGISTRY_BY_DB[dbname] = cls()
        return _REGISTRY_BY_DB[dbname]

    @classmethod
    def wipe_registry_for(cls, dbname):
        if dbname in _REGISTRY_BY_DB:
            del _REGISTRY_BY_DB[dbname]

    def ir_http_track(self, _id):
        self._http_ids.add(_id)

    def ir_http_seen(self, _id):
        return _id in self._http_ids

    @staticmethod
    def make_rule(*a, **kw):
        return EndpointRule(*a, **kw)


class EndpointRule:
    """Hold information for a custom endpoint rule."""

    __slots__ = ("key", "route", "endpoint", "routing", "endpoint_hash", "route_group")

    def __init__(self, key, route, endpoint, routing, endpoint_hash, route_group=None):
        self.key = key
        self.route = route
        self.endpoint = endpoint
        self.routing = routing
        self.endpoint_hash = endpoint_hash
        self.route_group = route_group

    def __repr__(self):
        return f"{self.key}: {self.route}" + (
            f"[{self.route_group}]" if self.route_group else ""
        )
