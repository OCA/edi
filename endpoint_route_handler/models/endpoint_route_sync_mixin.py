# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from functools import partial

from odoo import api, fields, models

from ..registry import EndpointRegistry

_logger = logging.getLogger(__file__)


class EndpointRouteSyncMixin(models.AbstractModel):
    """Mixin to handle synchronization of custom routes to the registry.

    Consumers of this mixin gain:

        * handling of sync state
        * sync helpers
        * automatic registration of routes on boot

    Consumers of this mixin must implement:

        * `_prepare_endpoint_rules` to retrieve all the `EndpointRule` to register
        * `_registered_endpoint_rule_keys` to retrieve all keys of registered rules
    """

    _name = "endpoint.route.sync.mixin"
    _description = "Endpoint Route sync mixin"

    active = fields.Boolean(default=True)
    registry_sync = fields.Boolean(
        help="ON: the record has been modified and registry was not notified."
        "\nNo change will be active until this flag is set to false via proper action."
        "\n\nOFF: record in line with the registry, nothing to do.",
        default=False,
        copy=False,
    )

    def write(self, vals):
        if any([x in vals for x in self._routing_impacting_fields() + ("active",)]):
            # Mark as out of sync
            vals["registry_sync"] = False
        res = super().write(vals)
        if vals.get("registry_sync"):
            # NOTE: this is not done on create to allow bulk reload of the envs
            # and avoid multiple env restarts in case of multiple edits
            # on one or more records in a row.
            self._add_after_commit_hook(self.ids)
        return res

    @api.model
    def _add_after_commit_hook(self, record_ids):
        self.env.cr.postcommit.add(
            partial(self._handle_registry_sync_post_commit, record_ids),
        )

    def _handle_registry_sync(self, record_ids=None):
        """Register and un-register controllers for given records."""
        record_ids = record_ids or self.ids
        _logger.info("%s sync registry for %s", self._name, str(record_ids))
        records = self.browse(record_ids).exists()
        records.filtered(lambda x: x.active)._register_controllers()
        records.filtered(lambda x: not x.active)._unregister_controllers()

    def _handle_registry_sync_post_commit(self, record_ids=None):
        """Handle registry sync after commit.

        When the sync is triggered as a post-commit hook
        the env has been flushed already and the cursor committed, of course.
        Hence, we must commit explicitly.
        """
        self._handle_registry_sync(record_ids=record_ids)
        self.env.cr.commit()  # pylint: disable=invalid-commit

    @property
    def _endpoint_registry(self):
        return EndpointRegistry.registry_for(self.env.cr)

    def _register_hook(self):
        super()._register_hook()
        if not self._abstract:
            # Ensure existing active records are loaded at startup.
            # Pass `init` to bypass routing map refresh
            # since this piece of code runs only when the model is loaded.
            domain = [("active", "=", True), ("registry_sync", "=", True)]
            self.search(domain)._register_controllers(init=True)

    def unlink(self):
        if not self._abstract:
            self._unregister_controllers()
        return super().unlink()

    def _register_controllers(self, init=False, options=None):
        if not self:
            return
        rules = self._prepare_endpoint_rules(options=options)
        self._endpoint_registry.update_rules(rules, init=init)
        if not init:
            # When envs are already loaded we must signal changes
            self._force_routing_map_refresh()
        _logger.debug(
            "%s registered controllers: %s",
            self._name,
            ", ".join([r.route for r in rules]),
        )

    def _force_routing_map_refresh(self):
        """Signal changes to make all routing maps refresh."""
        self.env["ir.http"]._clear_routing_map()  # TODO: redundant?
        self.env.registry.registry_invalidated = True
        self.env.registry.signal_changes()

    def _unregister_controllers(self):
        if not self:
            return
        self._endpoint_registry.drop_rules(self._registered_endpoint_rule_keys())

    def _routing_impacting_fields(self, options=None):
        """Return list of fields that have impact on routing for current record."""
        raise NotImplementedError()

    def _prepare_endpoint_rules(self, options=None):
        """Return list of `EndpointRule` instances for current record."""
        raise NotImplementedError()

    def _registered_endpoint_rule_keys(self):
        """Return list of registered `EndpointRule` unique keys for current record."""
        raise NotImplementedError()
