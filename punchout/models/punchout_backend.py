# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PunchoutBackend(models.Model):
    _name = "punchout.backend"
    _description = "PunchOut Backend"
    _sql_constraints = [
        ("name_unique", "unique(name)", _("This PunchOut backend already exists."))
    ]

    name = fields.Char(string="Name", required=True,)
    url = fields.Char(string="URL", required=True,)
    from_domain = fields.Char(string="From domain", required=True,)
    from_identity = fields.Char(string="From identity", required=True,)
    to_domain = fields.Char(string="To domain", required=True,)
    to_identity = fields.Char(string="To identity", required=True,)
    shared_secret = fields.Char(string="Shared secret", required=True,)
    user_agent = fields.Char(string="User agent", required=True,)
    deployment_mode = fields.Char(
        string="Deployment mode", help="Test or production", required=True,
    )
    browser_form_post_url = fields.Char(
        string="Browser form post URL",
        help="Exposed URL where the shopping cart must be sent back to.",
        required=True,
    )
    buyer_cookie_encryption_key = fields.Char(
        string="Key to encrypt the buyer cookie", required=True,
    )

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

        return "/".join([base_url, url, str(self.id)])

    def redirect_to_backend(self):
        self.ensure_one()
        return (
            self.env["punchout.request"]
            .with_context(punchout_backend_id=self.id,)
            ._redirect_to_punchout()
        )

    def _get_redirect_url(self):
        self.ensure_one()
        return "/web"
