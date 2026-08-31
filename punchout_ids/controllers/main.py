# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class PunchoutIdsController(Controller):
    @route(
        "/punchout/ids/receive/<int:backend_id>",
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
        """Receive IDS shopping cart response.

        IDS responses come with a 'warenkorb' parameter containing XML.
        """
        env = request.env
        backend = env["punchout.backend"].sudo().browse(backend_id)
        # IDS uses 'warenkorb' parameter for the shopping cart XML
        warenkorb = request.httprequest.form.get("warenkorb", "")
        try:
            backend._check_response_size(warenkorb)
        except Exception as e:  # noqa: BLE001
            _logger.error(
                "[punchout.ids.receive] backend=%s payload rejected: %s",
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
                backend_id, warenkorb, session_token=session_token
            )
        )
        if not punchout_session:
            redirect_url = backend._get_redirect_url()
            _logger.error(
                "[punchout.ids.receive] backend=%s no session matched. Data: %s",
                backend_id,
                warenkorb[:500] if warenkorb else "(empty)",
            )
        else:
            redirect_url = punchout_session._get_redirect_url()
        return request.redirect(redirect_url)
