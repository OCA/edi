# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import textwrap

import werkzeug

from odoo import _, api, exceptions, fields, http, models
from odoo.tools import safe_eval

from odoo.addons.rpc_helper.decorator import disable_rpc


@disable_rpc()  # Block ALL RPC calls
class EndpointMixin(models.AbstractModel):

    _name = "endpoint.mixin"
    _inherit = "endpoint.route.handler"
    _description = "Endpoint mixin"

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

    def _selection_exec_mode(self):
        return [("code", "Execute code")]

    def _compute_code_snippet_docs(self):
        for rec in self:
            rec.code_snippet_docs = textwrap.dedent(rec._default_code_snippet_docs())

    @api.constrains("exec_mode")
    def _check_exec_mode(self):
        for rec in self:
            rec._validate_exec_mode()

    def _validate_exec_mode(self):
        validator = getattr(self, "_validate_exec__" + self.exec_mode, lambda x: True)
        validator()

    def _validate_exec__code(self):
        if not self._code_snippet_valued():
            raise exceptions.UserError(
                _("Exec mode is set to `Code`: you must provide a piece of code")
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

        Use ``log`` function to log messages into ir.logging table.
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
            "log": self._code_snippet_log_func,
        }

    def _code_snippet_log_func(self, message, level="info"):
        # Almost barely copied from ir.actions.server
        with self.pool.cursor() as cr:
            cr.execute(
                """
                INSERT INTO ir_logging
                (create_date, create_uid, type, dbname, name, level, message, path, line, func)
                VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    self.env.uid,
                    "server",
                    self._cr.dbname,
                    __name__,
                    level,
                    message,
                    "endpoint",
                    self.id,
                    self.name,
                ),
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

    def _default_endpoint_options_handler(self):
        return {
            "klass_dotted_path": "odoo.addons.endpoint.controllers.main.EndpointController",
            "method_name": "auto_endpoint",
            "default_pargs": (self._name, self.route),
        }

    def _validate_request(self, request):
        http_req = request.httprequest
        if self.request_method and self.request_method != http_req.method:
            self._logger.error("_validate_request: MethodNotAllowed")
            raise werkzeug.exceptions.MethodNotAllowed()
        if (
            self.request_content_type
            and self.request_content_type != http_req.content_type
        ):
            self._logger.error("_validate_request: UnsupportedMediaType")
            raise werkzeug.exceptions.UnsupportedMediaType()

    def _get_handler(self):
        try:
            return getattr(self, "_handle_exec__" + self.exec_mode)
        except AttributeError:
            raise exceptions.UserError(
                _("Missing handler for exec mode %s") % self.exec_mode
            )

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

    def copy_data(self, default=None):
        result = super().copy_data(default=default)
        # `route` cannot be copied as it must me unique.
        # Yet, we want to be able to duplicate a record from the UI.
        for rec, data in zip(self, result):
            if not data.get("route"):
                data["route"] = f"{rec.route}/COPY_FIXME"
        return result
