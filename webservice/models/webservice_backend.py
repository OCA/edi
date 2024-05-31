# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# @author Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class WebserviceBackend(models.Model):

    _name = "webservice.backend"
    _inherit = ["collection.base", "server.env.techname.mixin", "server.env.mixin"]
    _description = "WebService Backend"

    name = fields.Char(required=True)
    tech_name = fields.Char(required=True)
    protocol = fields.Selection([("http", "HTTP Request")], required=True)
    url = fields.Char(required=True)
    auth_type = fields.Selection(
        selection=[
            ("none", "Public"),
            ("user_pwd", "Username & password"),
            ("api_key", "API Key"),
            ("oauth2", "OAuth2"),
        ],
        required=True,
    )
    username = fields.Char(auth_type="user_pwd")
    password = fields.Char(auth_type="user_pwd")
    api_key = fields.Char(string="API Key", auth_type="api_key")
    api_key_header = fields.Char(string="API Key header", auth_type="api_key")
    oauth2_flow = fields.Selection(
        [
            ("backend_application", "Backend Application (Client Credentials Grant)"),
            ("web_application", "Web Application (Authorization Code Grant)"),
        ],
        readonly=False,
    )
    oauth2_clientid = fields.Char(string="Client ID", auth_type="oauth2")
    oauth2_client_secret = fields.Char(string="Client Secret", auth_type="oauth2")
    oauth2_token_url = fields.Char(string="Token URL", auth_type="oauth2")
    oauth2_authorization_url = fields.Char(string="Authorization URL")
    oauth2_audience = fields.Char(
        string="Audience"
        # no auth_type because not required
    )
    oauth2_scope = fields.Char(help="scope of the the authorization")
    oauth2_token = fields.Char(help="the OAuth2 token (serialized JSON)")
    redirect_url = fields.Char(
        compute="_compute_redirect_url",
        help="The redirect URL to be used as part of the OAuth2 authorisation flow",
    )
    oauth2_state = fields.Char(
        help="random key generated when authorization flow starts "
        "to ensure that no CSRF attack happen"
    )
    content_type = fields.Selection(
        [
            ("application/json", "JSON"),
            ("application/xml", "XML"),
            ("application/x-www-form-urlencoded", "Form"),
        ],
        required=True,
    )
    company_id = fields.Many2one("res.company", string="Company")

    @api.constrains("auth_type")
    def _check_auth_type(self):
        valid_fields = {
            k: v for k, v in self._fields.items() if hasattr(v, "auth_type")
        }
        for rec in self:
            if rec.auth_type == "none":
                continue
            _fields = [v for v in valid_fields.values() if v.auth_type == rec.auth_type]
            missing = []
            for _field in _fields:
                if not rec[_field.name]:
                    missing.append(_field)
            if missing:
                raise exceptions.UserError(rec._msg_missing_auth_param(missing))

    def _msg_missing_auth_param(self, missing_fields):
        def get_selection_value(fname):
            return self._fields.get(fname).convert_to_export(self[fname], self)

        return _(
            "Webservice '%(name)s' requires '%(auth_type)s' authentication. "
            "However, the following field(s) are not valued: %(fields)s"
        ) % {
            "name": self.name,
            "auth_type": get_selection_value("auth_type"),
            "fields": ", ".join([f.string for f in missing_fields]),
        }

    def _valid_field_parameter(self, field, name):
        extra_params = ("auth_type",)
        return name in extra_params or super()._valid_field_parameter(field, name)

    def call(self, method, *args, **kwargs):
        _logger.debug("backend %s: call %s %s %s", self.name, method, args, kwargs)
        response = getattr(self._get_adapter(), method)(*args, **kwargs)
        _logger.debug("backend %s: response: \n%s", self.name, response)
        return response

    def _get_adapter(self):
        with self.work_on(self._name) as work:
            return work.component(
                usage="webservice.request",
                webservice_protocol=self._get_adapter_protocol(),
            )

    def _get_adapter_protocol(self):
        protocol = self.protocol
        if self.auth_type.startswith("oauth2"):
            protocol += f"+{self.auth_type}-{self.oauth2_flow}"
        return protocol

    @api.depends("auth_type", "oauth2_flow")
    def _compute_redirect_url(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        base_url = get_param("web.base.url")
        if base_url.startswith("http://"):
            _logger.warning(
                "web.base.url is configured in http. Oauth2 requires using https"
            )
            base_url = base_url[len("http://") :]
        if not base_url.startswith("https://"):
            base_url = f"https://{base_url}"
        for rec in self:
            if rec.auth_type == "oauth2" and rec.oauth2_flow == "web_application":
                rec.redirect_url = f"{base_url}/webservice/{rec.id}/oauth2/redirect"
            else:
                rec.redirect_url = False

    def button_authorize(self):
        _logger.info("Button OAuth2 Authorize")
        authorize_url = self._get_adapter().redirect_to_authorize()
        _logger.info("Redirecting to %s", authorize_url)
        return {
            "type": "ir.actions.act_url",
            "url": authorize_url,
            "target": "self",
        }

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        webservice_fields = {
            "protocol": {},
            "url": {},
            "auth_type": {},
            "username": {},
            "password": {},
            "api_key": {},
            "api_key_header": {},
            "content_type": {},
            "oauth2_flow": {},
            "oauth2_scope": {},
            "oauth2_clientid": {},
            "oauth2_client_secret": {},
            "oauth2_authorization_url": {},
            "oauth2_token_url": {},
            "oauth2_audience": {},
        }
        webservice_fields.update(base_fields)
        return webservice_fields

    def _compute_server_env(self):
        # OVERRIDE: reset ``oauth2_flow`` when ``auth_type`` is not "oauth2", even if
        # defined otherwise in server env vars
        res = super()._compute_server_env()
        self.filtered(lambda r: r.auth_type != "oauth2").oauth2_flow = None
        return res
