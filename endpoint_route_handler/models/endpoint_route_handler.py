# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, exceptions, fields, models

ENDPOINT_ROUTE_CONSUMER_MODELS = {
    # by db
}


class EndpointRouteHandler(models.AbstractModel):

    _name = "endpoint.route.handler"
    _inherit = "endpoint.route.sync.mixin"
    _description = "Endpoint Route handler"

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

    # TODO: add flag to prevent route updates on save ->
    # should be handled by specific actions + filter in a tree view + btn on form

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

    @api.depends(lambda self: self._routing_impacting_fields())
    def _compute_endpoint_hash(self):
        # Do not use read to be able to play this on NewId records too
        # (NewId records are classified as missing in ACL check).
        # values = self.read(self._routing_impacting_fields())
        values = [
            {fname: rec[fname] for fname in self._routing_impacting_fields()}
            for rec in self
        ]
        for rec, vals in zip(self, values):
            vals.pop("id", None)
            rec.endpoint_hash = hash(tuple(vals.values()))

    def _routing_impacting_fields(self):
        return ("route", "auth_type", "request_method")

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

    def _refresh_endpoint_data(self):
        """Enforce refresh of route computed fields.

        Required for NewId records when using this model as a tool.
        """
        self._compute_endpoint_hash()
        self._compute_route()

    def _register_controllers(self, init=False, options=None):
        if self and self._abstract:
            self._refresh_endpoint_data()
        super()._register_controllers(init=init, options=options)

    def _unregister_controllers(self):
        if self and self._abstract:
            self._refresh_endpoint_data()
        super()._unregister_controllers()

    def _prepare_endpoint_rules(self, options=None):
        return [rec._make_controller_rule(options=options) for rec in self]

    def _registered_endpoint_rule_keys(self):
        return tuple([rec._endpoint_registry_unique_key() for rec in self])

    def _endpoint_registry_unique_key(self):
        return "{0._name}:{0.id}".format(self)

    # TODO: consider if useful or not for single records
    def _register_single_controller(self, options=None, key=None, init=False):
        """Shortcut to register one single controller."""
        rule = self._make_controller_rule(options=options, key=key)
        self._endpoint_registry.update_rules([rule], init=init)
        self._logger.debug(
            "Registered controller %s (auth: %s)", self.route, self.auth_type
        )

    def _make_controller_rule(self, options=None, key=None):
        key = key or self._endpoint_registry_unique_key()
        route, routing, endpoint_hash = self._get_routing_info()
        options = options or self._default_endpoint_options()
        return self._endpoint_registry.make_rule(
            # fmt: off
            key,
            route,
            options,
            routing,
            endpoint_hash,
            route_group=self.route_group
            # fmt: on
        )

    def _default_endpoint_options(self):
        options = {"handler": self._default_endpoint_options_handler()}
        return options

    def _default_endpoint_options_handler(self):
        self._logger.warning(
            "No specific endpoint handler options defined for: %s, falling back to default",
            self._name,
        )
        base_path = "odoo.addons.endpoint_route_handler.controllers.main"
        return {
            "klass_dotted_path": f"{base_path}.EndpointNotFoundController",
            "method_name": "auto_not_found",
        }

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
