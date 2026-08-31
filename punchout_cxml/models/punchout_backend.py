# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PunchoutBackend(models.Model):
    _inherit = "punchout.backend"

    # cXML-specific credential fields
    from_domain = fields.Char(
        string="From domain",
        groups="base.group_system",
        help="cXML From credential domain (e.g., 'NetworkId').",
    )
    from_identity = fields.Char(
        string="From identity",
        groups="base.group_system",
        help="cXML From credential identity.",
    )
    to_domain = fields.Char(
        string="To domain",
        help="cXML To credential domain.",
    )
    to_identity = fields.Char(
        string="To identity",
        groups="base.group_system",
        help="cXML To credential identity.",
    )
    shared_secret = fields.Char(
        string="Shared secret",
        groups="base.group_system",
        help="cXML authentication shared secret.",
    )
    user_agent = fields.Char(
        string="User agent",
        help="User agent string for cXML requests.",
    )
    deployment_mode = fields.Char(
        string="Deployment mode",
        help="cXML deployment mode: 'test' or 'production'.",
    )

    # cXML DTD validation
    cxml_version = fields.Char(
        string="cXML Version",
        default="1.2.008",
        help="cXML DTD version.",
    )
    dtd_file = fields.Binary(
        string="DTD File for validation",
        groups="base.group_system",
        help="Optional DTD file for response validation.",
    )
    dtd_filename = fields.Char(
        groups="base.group_system",
    )

    def _get_domain_and_identity(self, credential_type):
        """Get cXML credential domain and identity."""
        self.ensure_one()
        if credential_type in ("From", "Sender"):
            return self.from_domain, self.from_identity
        if credential_type == "To":
            return self.to_domain, self.to_identity
        return False, False

    def _get_cxml_version(self):
        self.ensure_one()
        return self.cxml_version

    def _get_cxml_dtd_declaration(self):
        self.ensure_one()
        version = self._get_cxml_version()
        dtd_link = f"http://xml.cxml.org/schemas/cXML/{version}/cXML.dtd"
        declaration = f'<!DOCTYPE cXML SYSTEM "{dtd_link}">'
        return declaration

    def action_test_connection(self):
        """Send a real ``PunchOutSetupRequest`` and verify the supplier
        responds with a valid ``PunchOutSetupResponse``.

        Catches the most common pre-flight problems — wrong URL,
        wrong credentials, wrong shared secret, expired DTD link —
        before a user clicks Access and gets a confusing redirect
        failure mid-flow.

        Only meaningful for cXML (which has a real HTTP setup
        handshake). OCI/IDS just build a catalog URL on the client
        side, so there's nothing to round-trip; the equivalent there
        would be a generic URL ping, which is roughly worthless
        because the catalog page needs auth params and frequently
        only accepts POST.
        """
        self.ensure_one()
        if self.protocol != "cxml":
            raise UserError(
                _(
                    "Test Connection is only available for cXML backends. "
                    "OCI and IDS use client-side URL building, so there is "
                    "no setup handshake to test until the user actually "
                    "clicks Access."
                )
            )
        # Reuse the regular setup flow on a throw-away session — it
        # posts the real request, parses the real response, and stores
        # both for inspection. We then unlink the session so we don't
        # litter the table with "test" rows.
        session = (
            self.env["punchout.session"]
            .sudo()
            .create({"backend_id": self.id, "buyer_cookie_id": "TEST-CONNECTION"})
        )
        try:
            url = self.env["punchout.session"]._get_post_punchout_setup_url(session)
        except Exception as e:  # noqa: BLE001
            session.unlink()
            raise UserError(_("Test connection failed: %(err)s") % {"err": e}) from e
        session.unlink()
        if not url:
            raise UserError(
                _(
                    "Supplier responded but did not return a StartPage URL. "
                    "Check the supplier's logs."
                )
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Connection OK"),
                "message": _("Supplier responded with a valid setup response."),
                "type": "success",
                "sticky": False,
            },
        }
