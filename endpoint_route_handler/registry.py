# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

_REGISTRY_BY_DB = {}


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
        self._mapping = {}
        self._routing_update_required = False
        self._rules_to_load = []
        self._rules_to_drop = []

    def get_rules(self):
        return self._mapping.values()

    # TODO: add test
    def get_rules_by_group(self, group):
        for key, rule in self._mapping.items():
            if rule._endpoint_group == group:
                yield (key, rule)

    def add_or_update_rule(self, key, rule, force=False):
        existing = self._mapping.get(key)
        if not existing:
            self._mapping[key] = rule
            self._rules_to_load.append(rule)
            self._routing_update_required = True
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

    @classmethod
    def registry_for(cls, dbname):
        if dbname not in _REGISTRY_BY_DB:
            _REGISTRY_BY_DB[dbname] = cls()
        return _REGISTRY_BY_DB[dbname]

    @classmethod
    def wipe_registry_for(cls, dbname):
        if dbname in _REGISTRY_BY_DB:
            del _REGISTRY_BY_DB[dbname]
