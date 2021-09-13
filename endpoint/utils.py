# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

_ENDPOINT_ROUTING_MAP = {}


class EndpointRegistry:
    """Registry for endpoints.

    Used to:

    * track registered endpoints and their rules
    * track routes to be updated or deleted
    * retrieve routes to update for ir.http routing map

    When the flag ``_routing_update_required`` is ON
    the routing map will be forcedly refreshed.

    """

    def __init__(self):
        self._mapping = _ENDPOINT_ROUTING_MAP
        self._routing_update_required = False
        self._rules_to_load = []
        self._rules_to_drop = []

    def get_rules(self):
        return self._mapping.values()

    def add_or_update_rule(self, key, rule):
        existing = self._mapping.get(key)
        if not existing:
            self._mapping[key] = rule
            return True
        if existing._endpoint_hash != rule._endpoint_hash:
            # Override and set as to be updated
            self._rules_to_drop.append(existing)
            self._rules_to_load.append(rule)
            self._mapping[key] = rule
            self._routing_update_required = True
            return True

    def drop_rule(self, key):
        existing = self._mapping.get(key)
        if not existing:
            return False
        # Override and set as to be updated
        self._rules_to_drop.append(existing)
        self._routing_update_required = True
        return True

    def get_rules_to_update(self):
        return {
            "to_drop": self._rules_to_drop,
            "to_load": self._rules_to_load,
        }

    def routing_update_required(self):
        return self._routing_update_required

    def reset_update_required(self):
        self._routing_update_required = False
        self._rules_to_drop = []
        self._rules_to_load = []


endpoint_registry = EndpointRegistry()
