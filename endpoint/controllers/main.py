# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import json

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import Response, request


class EndpointControllerMixin:
    def _handle_endpoint(self, env, model, endpoint_route, **params):
        endpoint = self._find_endpoint(env, model, endpoint_route)
        if not endpoint:
            raise NotFound()
        endpoint._validate_request(request)
        result = endpoint._handle_request(request)
        return self._handle_result(result)

    def _handle_result(self, result):
        response = result.get("response")
        if isinstance(response, Response):
            # Full response already provided
            return response
        payload = result.get("payload", "")
        status = result.get("status_code", 200)
        headers = result.get("headers", {})
        return self._make_json_response(payload, headers=headers, status=status)

    # TODO: probably not needed anymore as controllers are automatically registered
    def _make_json_response(self, payload, headers=None, status=200, **kw):
        # TODO: guess out type?
        data = json.dumps(payload)
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        resp = request.make_response(data, headers=headers)
        resp.status = str(status)
        return resp

    def _find_endpoint(self, env, model, endpoint_route):
        return env[model]._find_endpoint(endpoint_route)

    def auto_endpoint(self, model, endpoint_route, **params):
        """Default method to handle auto-generated endpoints"""
        env = request.env
        return self._handle_endpoint(env, model, endpoint_route, **params)


class EndpointController(http.Controller, EndpointControllerMixin):
    pass
