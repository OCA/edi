# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WebserviceBackend(models.Model):

    _name = "webservice.backend"
    _inherit = ["collection.base", "server.env.techname.mixin", "server.env.mixin"]
    _description = "WebService Backend"

    name = fields.Char(required=True)
    tech_name = fields.Char(required=True)
    protocol = fields.Selection([("http", "HTTP Request")], required=True)
    url = fields.Char(required=True)
    username = fields.Char()
    password = fields.Char()
    content_type = fields.Selection(
        [
            ("application/json", "JSON"),
            ("application/xml", "XML"),
            ("application/x-www-form-urlencoded", "Form"),
        ],
        required=True,
    )

    def call(self, method, *args, **kwargs):
        return getattr(self._get_adapter(), method)(*args, **kwargs)

    def _get_adapter(self):
        with self.work_on(self._name) as work:
            return work.component(
                usage="webservice.request", webservice_protocol=self.protocol
            )

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        webservice_fields = {
            "protocol": {},
            "url": {},
            "username": {},
            "password": {},
            "content_type": {},
        }
        webservice_fields.update(base_fields)
        return webservice_fields
