# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, exceptions, fields, http, models

# from odoo.addons.base_sparse_field.models.fields import Serialized
from ..registry import EndpointRegistry

ENDPOINT_ROUTE_CONSUMER_MODELS = {
    # by db
}


class EndpointRouteHandler(models.AbstractModel):

    _name = "endpoint.route.handler"
    _description = "Endpoint Route handler"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    route = fields.Char(
        required=True,
        index=True,
        compute="_compute_route",
        inverse="_inverse_route",
        readonly=False,
        store=True,
        copy=False,
    )
    route_group = fields.Char(help="Use this to classify routes together")
    route_type = fields.Selection(selection="_selection_route_type", default="http")
    auth_type = fields.Selection(
        selection="_selection_auth_type", default="user_endpoint"
    )
    request_content_type = fields.Selection(selection="_selection_request_content_type")
    # TODO: this is limiting the possibility of supporting more than one method.
    request_method = fields.Selection(
        selection="_selection_request_method", required=True
    )
    # # TODO: validate params? Just for doc? Maybe use Cerberus?
    # # -> For now let the implementer validate the params in the snippet.
    # request_params = Serialized(help="TODO")

    endpoint_hash = fields.Char(
        compute="_compute_endpoint_hash", help="Identify the route with its main params"
    )

    csrf = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "endpoint_route_unique",
            "unique(route)",
            "You can register an endpoint route only once.",
        )
    ]

    @api.constrains("route")
    def _check_route_unique_across_models(self):
        """Make sure routes are unique across all models.

        The SQL constraint above, works only on one specific model/table.
        Here we check that routes stay unique across all models.
        This is mostly to make sure admins know that the route already exists
        somewhere else, because route controllers are registered only once
        for the same path.
        """
        # TODO: add tests registering a fake model.
        # However, @simahawk tested manually and it works.
        # TODO: shall we check for route existance in the registry instead?
        all_models = self._get_endpoint_route_consumer_models()
        routes = [x["route"] for x in self.read(["route"])]
        clashing_models = []
        for model in all_models:
            if model != self._name and self.env[model].sudo().search_count(
                [("route", "in", routes)]
            ):
                clashing_models.append(model)
        if clashing_models:
            raise exceptions.UserError(
                _(
                    "Non unique route(s): %(routes)s.\n"
                    "Found in model(s): %(models)s.\n"
                )
                % {"routes": ", ".join(routes), "models": ", ".join(clashing_models)}
            )

    def _get_endpoint_route_consumer_models(self):
        global ENDPOINT_ROUTE_CONSUMER_MODELS
        if ENDPOINT_ROUTE_CONSUMER_MODELS.get(self.env.cr.dbname):
            return ENDPOINT_ROUTE_CONSUMER_MODELS.get(self.env.cr.dbname)
        models = []
        route_model = "endpoint.route.handler"
        for model in self.env.values():
            if (
                model._name != route_model
                and not model._abstract
                and route_model in model._inherit
            ):
                models.append(model._name)
        ENDPOINT_ROUTE_CONSUMER_MODELS[self.env.cr.dbname] = models
        return models

    @property
    def _logger(self):
        return logging.getLogger(self._name)

    def _selection_route_type(self):
        return [("http", "HTTP"), ("json", "JSON")]

    def _selection_auth_type(self):
        return [("public", "Public"), ("user_endpoint", "User")]

    def _selection_request_method(self):
        return [
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ]

    def _selection_request_content_type(self):
        return [
            ("", "None"),
            ("text/plain", "Text"),
            ("text/csv", "CSV"),
            ("application/json", "JSON"),
            ("application/xml", "XML"),
            ("application/x-www-form-urlencoded", "Form"),
        ]

    @api.depends(lambda self: self._controller_fields())
    def _compute_endpoint_hash(self):
        # Do not use read to be able to play this on NewId records too
        # (NewId records are classified as missing in ACL check).
        # values = self.read(self._controller_fields())
        values = [
            {fname: rec[fname] for fname in self._controller_fields()} for rec in self
        ]
        for rec, vals in zip(self, values):
            vals.pop("id", None)
            rec.endpoint_hash = hash(tuple(vals.values()))

    def _controller_fields(self):
        return ["route", "auth_type", "request_method"]

    @api.depends("route")
    def _compute_route(self):
        for rec in self:
            rec.route = rec._clean_route()

    def _inverse_route(self):
        for rec in self:
            rec.route = rec._clean_route()

    # TODO: move to something better? Eg: computed field?
    # Shall we use the route_group? TBD!
    _endpoint_route_prefix = ""

    def _clean_route(self):
        route = (self.route or "").strip()
        if not route.startswith("/"):
            route = "/" + route
        prefix = self._endpoint_route_prefix
        if prefix and not route.startswith(prefix):
            route = prefix + route
        return route

    _blacklist_routes = ("/", "/web")  # TODO: what else?

    @api.constrains("route")
    def _check_route(self):
        for rec in self:
            if rec.route in self._blacklist_routes:
                raise exceptions.UserError(
                    _("`%s` uses a blacklisted routed = `%s`") % (rec.name, rec.route)
                )

    @api.constrains("request_method", "request_content_type")
    def _check_request_method(self):
        for rec in self:
            if rec.request_method in ("POST", "PUT") and not rec.request_content_type:
                raise exceptions.UserError(
                    _("Request method is required for POST and PUT.")
                )

    # Handle automatic route registration

    @api.model_create_multi
    def create(self, vals_list):
        rec = super().create(vals_list)
        if not self._abstract and rec.active:
            rec._register_controllers()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._handle_route_updates(vals)
        return res

    def _handle_route_updates(self, vals):
        if "active" in vals:
            if vals["active"]:
                self._register_controllers()
            else:
                self._unregister_controllers()
            return True
        if any([x in vals for x in self._controller_fields()]):
            self._register_controllers()
            return True
        return False

    def unlink(self):
        if not self._abstract:
            self._unregister_controllers()
        return super().unlink()

    def _register_hook(self):
        super()._register_hook()
        if not self._abstract:
            # Look explicitly for active records.
            # Pass `init` to not set the registry as updated
            # since this piece of code runs only when the model is loaded.
            self.search([("active", "=", True)])._register_controllers(init=True)

    def _register_controllers(self, init=False):
        if self._abstract:
            self._refresh_endpoint_data()
        for rec in self:
            rec._register_controller(init=init)

    def _unregister_controllers(self):
        if self._abstract:
            self._refresh_endpoint_data()
        for rec in self:
            rec._unregister_controller()

    def _refresh_endpoint_data(self):
        """Enforce refresh of route computed fields.

        Required for NewId records when using this model as a tool.
        """
        self._compute_endpoint_hash()
        self._compute_route()

    @property
    def _endpoint_registry(self):
        return EndpointRegistry.registry_for(self.env.cr.dbname)

    def _register_controller(self, endpoint_handler=None, key=None, init=False):
        rule = self._make_controller_rule(endpoint_handler=endpoint_handler, key=key)
        self._endpoint_registry.add_or_update_rule(rule, init=init)
        self._logger.debug(
            "Registered controller %s (auth: %s)", self.route, self.auth_type
        )

    def _make_controller_rule(self, endpoint_handler=None, key=None):
        key = key or self._endpoint_registry_unique_key()
        route, routing, endpoint_hash = self._get_routing_info()
        endpoint_handler = endpoint_handler or self._default_endpoint_handler()
        assert callable(endpoint_handler)
        endpoint = http.EndPoint(endpoint_handler, routing)
        rule = self._endpoint_registry.make_rule(
            # fmt: off
            key,
            route,
            endpoint,
            routing,
            endpoint_hash,
            route_group=self.route_group
            # fmt: on
        )
        return rule

    def _default_endpoint_handler(self):
        """Provide default endpoint handler.

        :return: bound method of a controller (eg: MyController()._my_handler)
        """
        raise NotImplementedError("No default endpoint handler defined.")

    def _get_routing_info(self):
        route = self.route
        routing = dict(
            type=self.route_type,
            auth=self.auth_type,
            methods=[self.request_method],
            routes=[route],
            csrf=self.csrf,
        )
        return route, routing, self.endpoint_hash

    def _endpoint_registry_unique_key(self):
        return "{0._name}:{0.id}".format(self)

    def _unregister_controller(self, key=None):
        key = key or self._endpoint_registry_unique_key()
        self._endpoint_registry.drop_rule(key)
