# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class PunchoutOciController(Controller):
    @route(
        "/punchout/oci/receive/<int:backend_id>",
        type="http",
        auth="none",
        methods=["POST"],
        save_session=False,
        csrf=False,
        # We write (state flip + row lock) on every call, so opt out
        # of Odoo 18's speculative read-only cursor — otherwise the
        # SELECT FOR UPDATE forces a costly retry-with-rw-cursor on
        # every supplier callback (and emits a WARNING that trips
        # OCA's CI log scanner).
        readonly=False,
    )
    def receive_punchout_response(self, backend_id, *args, **kwargs):
        """Receive OCI shopping cart response.

        OCI responses come as form data with NEW_ITEM- prefixed parameters.
        Example: NEW_ITEM-DESCRIPTION[1]=Product, NEW_ITEM-QUANTITY[1]=10

        ``punchout_session_token`` (added to HOOK_URL when the session
        was created) lets us pin the cart to the originating session
        unambiguously. Without it we fall back to the legacy
        "most recent draft session for this backend" lookup, which
        can mis-route concurrent sessions.
        """
        env = request.env
        backend = env["punchout.backend"].sudo().browse(backend_id)
        form_data = dict(request.httprequest.form)
        response_data = json.dumps(form_data)
        try:
            backend._check_response_size(response_data)
        except Exception as e:  # noqa: BLE001
            _logger.error(
                "[punchout.oci.receive] backend=%s payload rejected: %s",
                backend_id,
                e,
            )
            return request.redirect(backend._get_redirect_url())

        session_token = (
            request.params.get("punchout_session_token")
            or kwargs.get("punchout_session_token")
            or ""
        )
        punchout_session = (
            env["punchout.session"]
            .sudo()
            ._store_punchout_session_response(
                backend_id, response_data, session_token=session_token
            )
        )
        if not punchout_session:
            redirect_url = backend._get_redirect_url()
            _logger.error(
                "[punchout.oci.receive] backend=%s token=%s no session matched. "
                "Form data: %s",
                backend_id,
                session_token or "(none)",
                response_data,
            )
        else:
            redirect_url = punchout_session._get_redirect_url()
        return request.redirect(redirect_url)
