# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import werkzeug

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class PunchoutController(Controller):
    @route(
        "/punchout/cxml/receive/<int:backend_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def receive_punchout_response(self, backend_id, *args, **kwargs):
        cxml_string = kwargs.get("cxml-urlencoded")
        punchout_request = (
            request.env["punchout.request"]
            .sudo()
            ._store_punchout_request(backend_id, cxml_string)
        )
        if not punchout_request:
            _logger.error(
                "Unable to link the punchout response to a punchout.request "
                "with given XML: \n%s",
                cxml_string,
            )
        return werkzeug.utils.redirect("/web")
