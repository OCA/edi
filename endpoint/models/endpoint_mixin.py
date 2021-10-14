# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import textwrap
from functools import partial

import werkzeug
from werkzeug.routing import Rule

from odoo import _, api, exceptions, fields, http, models
from odoo.tools import safe_eval

from odoo.addons.base_sparse_field.models.fields import Serialized

from ..controllers.main import EndpointController
from ..utils import endpoint_registry

ENDPOINT_MIXIN_CONSUMER_MODELS = []


class EndpointMixin(models.AbstractModel):

    _name = "endpoint.mixin"
    _description = "Endpoint mixin"

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
    route_type = fields.Selection(selection="_selection_route_type", default="http")
    auth_type = fields.Selection(
        selection="_selection_auth_type", default="user_endpoint"
    )

    options = Serialized()
    request_content_type = fields.Selection(
        selection="_selection_request_content_type", sparse="options"
    )
    request_method = fields.Selection(
        selection="_selection_request_method", sparse="options", required=True
    )
    # # TODO: validate params? Just for doc? Maybe use Cerberus?
    # # -> For now let the implementer validate the params in the snippet.
    # request_params = fields.Char(help="TODO", sparse="options")

    exec_mode = fields.Selection(
        selection="_selection_exec_mode",
        required=True,
    )
    code_snippet = fields.Text()
    code_snippet_docs = fields.Text(
        compute="_compute_code_snippet_docs",
        default=lambda self: self._default_code_snippet_docs(),
    )
    exec_as_user_id = fields.Many2one(comodel_name="res.users")

    endpoint_hash = fields.Char(compute="_compute_endpoint_hash")

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
        all_models = self._get_endpoint_mixin_consumer_models()
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

    def _get_endpoint_mixin_consumer_models(self):
        global ENDPOINT_MIXIN_CONSUMER_MODELS
        if ENDPOINT_MIXIN_CONSUMER_MODELS:
            return ENDPOINT_MIXIN_CONSUMER_MODELS
        models = []
        mixin_name = "endpoint.mixin"
        for model in self.env.values():
            if model._name != mixin_name and mixin_name in model._inherit:
                models.append(model._name)
        ENDPOINT_MIXIN_CONSUMER_MODELS = models
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

    # TODO: Is this needed at all since we can cook full responses?
    def _selection_response_content_type(self):
        return [
            # TODO: how to get a complete list?
            # OR: shall we leave the text free?
            ("text/plain", "Plain text"),
            ("application/json", "JSON"),
            ("application/xml", "XML"),
        ]

    def _selection_exec_mode(self):
        return [("code", "Execute code")]

    def _compute_code_snippet_docs(self):
        for rec in self:
            rec.code_snippet_docs = textwrap.dedent(rec._default_code_snippet_docs())

    @api.depends(lambda self: self._controller_fields())
    def _compute_endpoint_hash(self):
        values = self.read(self._controller_fields())
        for rec, vals in zip(self, values):
            vals.pop("id", None)
            rec.endpoint_hash = hash(tuple(vals.values()))

    @api.depends("route")
    def _compute_route(self):
        for rec in self:
            rec.route = rec._clean_route()

    def _inverse_route(self):
        for rec in self:
            rec.route = rec._clean_route()

    _endpoint_route_prefix = ""
    """Prefix for all routes, includes slashes.
    """

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

    @api.constrains("exec_mode")
    def _check_exec_mode(self):
        for rec in self:
            rec._validate_exec_mode()

    def _validate_exec_mode(self):
        validator = getattr(self, "_validate_exec__" + self.exec_mode, lambda x: True)
        validator()

    def _validate_exec__code(self):
        if self.exec_mode == "code" and not self._code_snippet_valued():
            raise exceptions.UserError(
                _("Exec mode is set to `Code`: you must provide a piece of code")
            )

    @api.constrains("request_method", "request_content_type")
    def _check_request_method(self):
        for rec in self:
            if rec.request_method in ("POST", "PUT") and not rec.request_content_type:
                raise exceptions.UserError(
                    _("Request method is required for POST and PUT.")
                )

    @api.constrains("auth_type")
    def _check_auth(self):
        for rec in self:
            if rec.auth_type == "public" and not rec.exec_as_user_id:
                raise exceptions.UserError(
                    _("'Exec as user' is mandatory for public endpoints.")
                )

    def _default_code_snippet_docs(self):
        return """
        Available vars:

        * env
        * endpoint
        * request
        * datetime
        * dateutil
        * time
        * user
        * json
        * Response
        * werkzeug
        * exceptions

        Must generate either an instance of ``Response`` into ``response`` var or:

        * payload
        * headers
        * status_code

        which are all optional.
        """

    def _get_code_snippet_eval_context(self, request):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        return {
            "env": self.env,
            "user": self.env.user,
            "endpoint": self,
            "request": request,
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "json": safe_eval.json,
            "Response": http.Response,
            "werkzeug": safe_eval.wrap_module(
                werkzeug, {"exceptions": ["NotFound", "BadRequest", "Unauthorized"]}
            ),
            "exceptions": safe_eval.wrap_module(
                exceptions, ["UserError", "ValidationError"]
            ),
        }

    def _get_handler(self):
        try:
            return getattr(self, "_handle_exec__" + self.exec_mode)
        except AttributeError:
            raise exceptions.UserError(
                _("Missing handler for exec mode %s") % self.exec_mode
            )

    def _handle_exec__code(self, request):
        if not self._code_snippet_valued():
            return {}
        eval_ctx = self._get_code_snippet_eval_context(request)
        snippet = self.code_snippet
        safe_eval.safe_eval(snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result")
        if not isinstance(result, dict):
            raise exceptions.UserError(
                _("code_snippet should return a dict into `result` variable.")
            )
        return result

    def _code_snippet_valued(self):
        snippet = self.code_snippet or ""
        return bool(
            [
                not line.startswith("#")
                for line in (snippet.splitlines())
                if line.strip("")
            ]
        )

    def _validate_request(self, request):
        http_req = request.httprequest
        # TODO: likely not needed anymore
        if self.auth_type != "public" and not request.env.user:
            raise werkzeug.exceptions.Unauthorized()
        if self.request_method and self.request_method != http_req.method:
            self._logger.error("_validate_request: MethodNotAllowed")
            raise werkzeug.exceptions.MethodNotAllowed()
        if (
            self.request_content_type
            and self.request_content_type != http_req.content_type
        ):
            self._logger.error("_validate_request: UnsupportedMediaType")
            raise werkzeug.exceptions.UnsupportedMediaType()

    def _handle_request(self, request):
        # Switch user for the whole process
        self_with_user = self
        if self.exec_as_user_id:
            self_with_user = self.with_user(user=self.exec_as_user_id)
        handler = self_with_user._get_handler()
        try:
            res = handler(request)
        except self._bad_request_exceptions() as orig_exec:
            self._logger.error("_validate_request: BadRequest")
            raise werkzeug.exceptions.BadRequest() from orig_exec
        return res

    def _bad_request_exceptions(self):
        return (exceptions.UserError, exceptions.ValidationError)

    @api.model
    def _find_endpoint(self, endpoint_route):
        return self.sudo().search(self._find_endpoint_domain(endpoint_route), limit=1)

    def _find_endpoint_domain(self, endpoint_route):
        return [("route", "=", endpoint_route)]

    # Handle automatic route registration

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if not self._abstract:
            res._register_controllers()
        return res

    def write(self, vals):
        res = super().write(vals)
        if not self._abstract and any([x in vals for x in self._controller_fields()]):
            self._register_controllers()
        return res

    def unlink(self):
        if not self._abstract:
            for rec in self:
                rec._drop_controller_rule()
        return super().unlink()

    def _controller_fields(self):
        return ["route", "auth_type", "request_method"]

    def _register_hook(self):
        super()._register_hook()
        if not self._abstract:
            self.search([])._register_controllers()

    def _register_controllers(self):
        for rec in self:
            rec._register_controller()

    def _register_controller(self):
        rule = self._make_controller_rule()
        self._add_or_update_controller_rule(rule)
        self._logger.info(
            "Registered controller %s (auth: %s)", self.route, self.auth_type
        )

    _endpoint_base_controller_class = EndpointController

    def _make_controller_rule(self):
        route, routing = self._get_routing_info()
        base_controller = self._endpoint_base_controller_class()
        endpoint = http.EndPoint(
            partial(base_controller.auto_endpoint, self.route), routing
        )
        rule = Rule(route, endpoint=endpoint, methods=routing["methods"])
        rule.merge_slashes = False
        rule._auto_endpoint = True
        rule._endpoint_hash = self.endpoint_hash
        return rule

    def _get_routing_info(self):
        route = self.route
        routing = dict(
            type=self.route_type,
            auth=self.auth_type,
            methods=[self.request_method],
            routes=[route],
            # TODO: make this configurable
            # in case the endpoint is used for frontend stuff.
            csrf=False,
        )
        return route, routing

    def _add_or_update_controller_rule(self, rule):
        key = "{0._name}:{0.id}".format(self)
        endpoint_registry.add_or_update_rule(key, rule)

    def _drop_controller_rule(self):
        key = "{0._name}:{0.id}".format(self)
        endpoint_registry.drop_rule(key)
