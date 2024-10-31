# Copyright 2024 Camptocamp SA
# @author Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging

from oauthlib.oauth2.rfc6749 import errors
from werkzeug.urls import url_encode

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OAuth2Controller(http.Controller):
    @http.route(
        "/webservice/<int:backend_id>/oauth2/redirect",
        type="http",
        auth="public",
        csrf=False,
    )
    def redirect(self, backend_id, **params):
        backend = request.env["webservice.backend"].browse(backend_id).sudo()
        if backend.auth_type != "oauth2" or backend.oauth2_flow != "web_application":
            _logger.error("unexpected backed config for backend %d", backend_id)
            raise errors.MismatchingRedirectURIError()
        expected_state = backend.oauth2_state
        state = params.get("state")
        if state != expected_state:
            _logger.error("unexpected state: %s", state)
            raise errors.MismatchingStateError()
        code = params.get("code")
        adapter = (
            backend._get_adapter()
        )  # we expect an adapter that supports web_application
        token = adapter._fetch_token_from_authorization(code)
        backend.write({"oauth2_token": json.dumps(token), "oauth2_state": False})
        # after saving the token, redirect to the backend form view
        uid = request.session.uid
        user = request.env["res.users"].sudo().browse(uid)
        cids = request.httprequest.cookies.get("cids", str(user.company_id.id))
        cids = [int(cid) for cid in cids.split(",")]
        record_action = backend.get_access_action()
        url_params = {
            "model": backend._name,
            "id": backend.id,
            "active_id": backend.id,
            "action": record_action.get("id"),
        }
        view_id = backend.get_formview_id()
        if view_id:
            url_params["view_id"] = view_id

        if cids:
            url_params["cids"] = ",".join([str(cid) for cid in cids])
        url = "/web?#%s" % url_encode(url_params)
        return request.redirect(url)
