# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PunchoutBackend(models.Model):
    _name = "punchout.backend"
    _description = "PunchOut Backend"
    _sql_constraints = [
        ("name_unique", "unique(name)", _("This PunchOut backend already exists."))
    ]

    name = fields.Char(
        required=True,
    )
    description = fields.Char(
        required=True,
    )
    url = fields.Char(
        string="URL",
        required=True,
    )
    from_domain = fields.Char(
        string="From domain",
        required=True,
        groups="base.group_system",
    )
    from_identity = fields.Char(
        string="From identity",
        required=True,
        groups="base.group_system",
    )
    to_domain = fields.Char(
        string="To domain",
        required=True,
    )
    to_identity = fields.Char(
        string="To identity",
        required=True,
        groups="base.group_system",
    )
    shared_secret = fields.Char(
        string="Shared secret",
        required=True,
        groups="base.group_system",
    )
    user_agent = fields.Char(
        string="User agent",
        required=True,
    )
    deployment_mode = fields.Char(
        string="Deployment mode",
        help="Test or production",
        required=True,
    )
    browser_form_post_url = fields.Char(
        string="Browser form post URL",
        help="Exposed URL where the shopping cart must be sent back to.",
        required=True,
    )
    dtd_version = fields.Char(
        default="1.2.008",
    )
    dtd_file = fields.Binary(
        string="DTD File for validation",
        groups="base.group_system",
    )
    dtd_filename = fields.Char(
        groups="base.group_system",
    )
    state = fields.Selection(selection="_selection_state", default="draft")
    session_duration = fields.Integer(
        string="Maximum session duration",
        default=7200,
    )

    @api.constrains("session_duration")
    def _check_session_duration(self):
        for rec in self:
            if rec.session_duration <= 0:
                raise ValidationError(
                    _(
                        "The duration of the session must be greater than 0. {name}"
                    ).format(name=rec.display_name)
                )

    @api.model
    def _selection_state(self):
        return [
            ("draft", _("Draft")),
            ("open", _("Open")),
            ("closed", _("Closed")),
        ]

    def _get_domain_and_identity(self, credential_type):
        self.ensure_one()
        if credential_type in ("From", "Sender"):
            return self.from_domain, self.from_identity
        if credential_type == "To":
            return self.to_domain, self.to_identity
        return False, False

    def _get_browser_form_post_url(self):
        self.ensure_one()
        url = self.browser_form_post_url
        if url and url.startswith("http://") or url.startswith("https://"):
            return url
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if base_url.endswith("/"):
            base_url = "".join(base_url[:-1])
        if url and url.startswith("/"):
            url = "".join(url[1:])
        if not url:
            raise UserError(
                _(
                    f"Browser form post url is not configured on "
                    f"the backend. {self.display_name}"
                )
            )

        return "/".join([base_url, url, str(self.id), f"?db={self.env.cr.dbname}"])

    def _check_access_backend(self):
        """
        Inherit this method to check if current user can access
        the backend website
        """
        return True

    def redirect_to_backend(self):
        self.ensure_one()
        self._check_access_backend()
        return (
            self.env["punchout.session"]
            .with_context(
                punchout_backend_id=self.id,
            )
            ._redirect_to_punchout()
        )

    def _get_redirect_url(self):
        self.ensure_one()
        return "/web"

    def _get_cxml_version(self):
        self.ensure_one()
        return self.dtd_version

    def _get_cxml_dtd_declaration(self):
        self.ensure_one()
        version = self._get_cxml_version()
        dtd_link = f"http://xml.cxml.org/schemas/cXML/{version}/cXML.dtd"
        declaration = f'<!DOCTYPE cXML SYSTEM "{dtd_link}">'
        return declaration
