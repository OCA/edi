# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _get_post_punchout_setup_url(self, session):
        """Build OCI catalog URL with authentication and HOOK_URL parameters.

        For OCI, we don't POST a setup request. Instead, we build a URL that:
        1. Points to the vendor's catalog
        2. Includes authentication parameters
        3. Includes HOOK_URL for the return endpoint
        """
        if session.backend_id.protocol != "oci":
            return super()._get_post_punchout_setup_url(session)

        backend = session.backend_id
        base_url = backend.url
        if not base_url:
            raise UserError(
                _("OCI catalog URL not configured on backend %(name)s.")
                % {"name": backend.display_name}
            )

        # Parse existing URL and query string
        parsed = urlparse(base_url)
        existing_params = parse_qs(parsed.query)

        # Build new parameters
        params = {}
        for key, value in existing_params.items():
            params[key] = value[0] if len(value) == 1 else value

        # Add custom parameters from backend
        if backend.oci_custom_parameters:
            custom_params = parse_qs(backend.oci_custom_parameters)
            for key, value in custom_params.items():
                params[key] = value[0] if len(value) == 1 else value

        # Add HOOK_URL - where the cart will be returned. Append the
        # session's buyer cookie as ``punchout_session_token`` so the
        # receive controller can pin the returning cart to *this*
        # session even when several concurrent sessions exist for the
        # same backend (OCI has no built-in correlator like cXML's
        # BuyerCookie element, so we smuggle one in the URL).
        hook_url = backend._get_browser_form_post_url()
        sep = "&" if "?" in hook_url else "?"
        hook_url = f"{hook_url}{sep}punchout_session_token={session.buyer_cookie_id}"
        params["HOOK_URL"] = hook_url

        # Add OCI version info if needed
        if backend.oci_version:
            params.setdefault("OCI_VERSION", backend.oci_version)

        # Rebuild URL with all parameters
        new_query = urlencode(params)
        new_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, "", new_query, "")
        )

        # Store the setup request info
        session.write(
            {
                "setup_request": f"OCI Catalog URL: {new_url}",
            }
        )

        return new_url

    @api.model
    def _store_punchout_session_response(
        self, backend_id, response_data, session_token=None
    ):
        """Store OCI response and find matching session.

        Lookup order:
        1. ``session_token`` (the buyer cookie threaded through HOOK_URL
           on setup) — unambiguous, preferred.
        2. Most recent draft session for this backend — legacy fallback,
           kept for backward compatibility with backends that were
           configured before the token mechanism existed.

        The session row is locked ``FOR UPDATE`` while we flip its
        state, so concurrent callbacks for the same session can't
        race each other into double-processing.
        """
        backend = self.env["punchout.backend"].sudo().browse(backend_id)
        if backend.protocol != "oci":
            return super()._store_punchout_session_response(backend_id, response_data)

        domain = [("backend_id", "=", backend_id)]
        if session_token:
            domain.append(("buyer_cookie_id", "=", session_token))
        else:
            domain += [
                ("state", "=", "draft"),
                ("expiration_date", ">", fields.Datetime.now()),
            ]
        session = self.sudo().search(domain, order="create_date desc", limit=1)

        if not session:
            _logger.error(
                "[punchout.oci.match] backend=%s token=%s no session found",
                backend_id,
                session_token or "(none)",
            )
            return False
        # Lock the row so a concurrent callback for the same session
        # waits here instead of double-processing.
        self.env.cr.execute(
            "SELECT id FROM punchout_session WHERE id = %s FOR UPDATE",
            (session.id,),
        )

        # Parse and store the form data
        try:
            if isinstance(response_data, str):
                form_data = json.loads(response_data)
            else:
                form_data = response_data
        except (json.JSONDecodeError, TypeError):
            form_data = {"raw": str(response_data)}

        session.write(
            {
                "response": json.dumps(form_data, indent=2),
                "response_date": fields.Datetime.now(),
            }
        )

        # Validate and update state
        validation = session._validate_response()
        if validation.get("valid"):
            session.write({"state": "to_process"})
        else:
            session.write({"state": "error", "error_message": validation.get("error")})

        return session

    def _validate_response(self):
        """Validate OCI response contains required fields."""
        self.ensure_one()
        if self.backend_id.protocol != "oci":
            return super()._validate_response()

        if not self.response:
            return {"valid": False, "error": "Empty response"}

        try:
            form_data = json.loads(self.response)
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"Invalid JSON: {e}"}

        # Check for at least one NEW_ITEM entry
        has_items = any(key.startswith("NEW_ITEM-") for key in form_data.keys())
        if not has_items:
            return {"valid": False, "error": "No NEW_ITEM entries found in response"}

        return {"valid": True}
