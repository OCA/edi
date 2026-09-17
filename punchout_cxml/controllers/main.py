# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from base64 import b64decode

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class PunchoutCxmlController(Controller):
    @route(
        "/punchout/cxml/receive/<int:backend_id>",
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
        """Receive cXML PunchOutOrderMessage response."""
        env = request.env
        backend = env["punchout.backend"].sudo().browse(backend_id)
        cxml_b64_string = kwargs.get("cXML-base64")
        cxml_string = False
        if cxml_b64_string:
            cxml_string = b64decode(cxml_b64_string)
        cxml_string = cxml_string or kwargs.get("cxml-urlencoded")
        try:
            backend._check_response_size(cxml_string)
        except Exception as e:  # noqa: BLE001
            _logger.error(
                "[punchout.cxml.receive] backend=%s payload rejected: %s",
                backend_id,
                e,
            )
            return request.redirect(backend._get_redirect_url())
        punchout_session = (
            env["punchout.session"]
            .sudo()
            ._store_punchout_session_response(backend_id, cxml_string)
        )
        if not punchout_session:
            redirect_url = backend._get_redirect_url()
            _logger.error(
                "[punchout.cxml.receive] backend=%s no session matched. XML: %s",
                backend_id,
                cxml_string,
            )
        else:
            redirect_url = punchout_session._get_redirect_url()
        return request.redirect_query(redirect_url)
