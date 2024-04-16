# Copyright 2024 Camptocamp SA
# @author Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from oauthlib.oauth2.rfc6749 import errors

from odoo import http

_logger = logging.getLogger(__name__)


class OAuth2Controller(http.Controller):
    @http.route(
        "/webservice/{backend_id}/oauth2/redirect",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def redirect(self, backend_id, **params):
        backend = self.env["webservice.backend"].browse(backend_id).sudo()
        if backend.auth_type != "oauth2" or backend.oauth2_flow != "authorization_code":
            _logger.error("unexpected backed config for backend %d", backend_id)
            raise errors.MismatchingRedirectURIError()
        expected_state = backend.oauth2_state
        state = params.get("state")
        if state != expected_state:
            _logger.error("unexpected state: %s", state)
            raise errors.MismatchingStateError()
        params.get("code")
        adapter = (
            backend.get_adapter()
        )  # if expect an adapter support authorization_code
        adapter._fetch_token_from_authorization()
        action = self.env["ir.action"]._for_xml_id(
            "webservice.webservice_backend_act_window"
        )
        action["res_id"] = backend_id
        return action
