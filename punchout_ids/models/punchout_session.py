# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from lxml import objectify
from lxml.etree import XMLSyntaxError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _get_post_punchout_setup_url(self, session):
        """Build IDS catalog URL with authentication parameters.

        IDS (German standard) uses URL parameters for authentication.
        Common parameters: name_kunde, kndnr, pw_kunde
        """
        if session.backend_id.protocol != "ids":
            return super()._get_post_punchout_setup_url(session)

        backend = session.backend_id
        base_url = backend.url
        if not base_url:
            raise UserError(
                _("IDS catalog URL not configured on backend %(name)s.")
                % {"name": backend.display_name}
            )

        # Parse existing URL and query string
        parsed = urlparse(base_url)
        existing_params = parse_qs(parsed.query)

        # Build new parameters
        params = {}
        for key, value in existing_params.items():
            params[key] = value[0] if len(value) == 1 else value

        # Add IDS-specific authentication parameters
        if backend.ids_name_kunde:
            params["name_kunde"] = backend.ids_name_kunde
        if backend.ids_kndnr:
            params["kndnr"] = backend.ids_kndnr
        if backend.ids_pw_kunde:
            params["pw_kunde"] = backend.ids_pw_kunde

        # Add HOOK_URL - where the cart will be returned. Append the
        # session's buyer cookie as ``punchout_session_token`` so the
        # receive controller can pin the returning cart to *this*
        # session (IDS, like OCI, has no built-in correlator).
        hook_url = backend._get_browser_form_post_url()
        sep = "&" if "?" in hook_url else "?"
        hook_url = f"{hook_url}{sep}punchout_session_token={session.buyer_cookie_id}"
        params["hook_url"] = hook_url

        # Add IDS version if configured
        if backend.ids_version:
            params.setdefault("ids_version", backend.ids_version)

        # Rebuild URL with all parameters
        new_query = urlencode(params)
        new_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, "", new_query, "")
        )

        # Store the setup request info
        session.write(
            {
                "setup_request": f"IDS Catalog URL: {new_url}",
            }
        )

        return new_url

    @api.model
    def _store_punchout_session_response(
        self, backend_id, response_data, session_token=None
    ):
        """Store IDS response (warenkorb XML) and find matching session.

        Lookup order: explicit ``session_token`` (threaded via
        HOOK_URL on setup) first, then legacy "most recent draft
        session for this backend" fallback. Row-locked while we flip
        state to defend against concurrent callbacks racing.
        """
        backend = self.env["punchout.backend"].sudo().browse(backend_id)
        if backend.protocol != "ids":
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
                "[punchout.ids.match] backend=%s token=%s no session found",
                backend_id,
                session_token or "(none)",
            )
            return False
        # Row lock to prevent concurrent callbacks from double-processing.
        self.env.cr.execute(
            "SELECT id FROM punchout_session WHERE id = %s FOR UPDATE",
            (session.id,),
        )

        # Store the XML response
        xml_data = response_data
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode("utf-8")

        session.write(
            {
                "response": xml_data,
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
        """Validate IDS response is valid XML with order items."""
        self.ensure_one()
        if self.backend_id.protocol != "ids":
            return super()._validate_response()

        if not self.response:
            return {"valid": False, "error": "Empty response"}

        try:
            xml_data = self.response
            if isinstance(xml_data, str):
                xml_data = xml_data.encode("utf-8")
            order = objectify.fromstring(xml_data)

            # Check for Order and OrderItem elements
            if not hasattr(order, "Order"):
                return {"valid": False, "error": "No Order element found in response"}
            if not hasattr(order.Order, "OrderItem"):
                return {
                    "valid": False,
                    "error": "No OrderItem elements found in response",
                }

            return {"valid": True}

        except XMLSyntaxError as e:
            return {"valid": False, "error": f"Invalid XML: {e}"}
        except Exception as e:
            _logger.exception("Error validating IDS response")
            return {"valid": False, "error": str(e)}
