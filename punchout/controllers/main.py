# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from base64 import b64decode

from odoo.http import Controller, local_redirect, request, route

_logger = logging.getLogger(__name__)


class PunchoutController(Controller):
    @route(
        "/punchout/cxml/receive/<int:backend_id>",
        type="http",
        auth="none",
        methods=["POST"],
        save_session=False,
        csrf=False,
    )
    def receive_punchout_response(self, backend_id, *args, **kwargs):
        env = request.env
        cxml_b64_string = kwargs.get("cXML-base64")
        cxml_string = False
        if cxml_b64_string:
            cxml_string = b64decode(cxml_b64_string)
        cxml_string = cxml_string or kwargs.get("cxml-urlencoded")
        punchout_session = (
            env["punchout.session"]
            .sudo()
            ._store_punchout_session_response(backend_id, cxml_string)
        )
        backend = env["punchout.backend"].sudo().browse(backend_id)
        if not punchout_session:
            redirect_url = backend._get_redirect_url()
            _logger.error(
                "Unable to link the punchout response to a punchout.request "
                "with given XML: \n%s",
                cxml_string,
            )
        else:
            redirect_url = punchout_session._get_redirect_url()
        return local_redirect(redirect_url)
