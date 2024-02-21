# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo.addons.component.core import Component

from ..utils import sanitize_url_for_log

_logger = logging.getLogger(__name__)


class BaseRestRequestsAdapter(Component):
    """Generic adapter for HTTP requests."""

    _name = "base.request"
    _inherit = "base.webservice.adapter"
    _webservice_protocol = "http"

    # TODO: url and url_params could come from work_ctx
    def _request(self, method, url=None, url_params=None, **kwargs):
        url = self._get_url(url=url, url_params=url_params)
        # TODO: turn on/off debug from webservice setting?
        url_to_log = self._sanitize_url_for_log(url)
        _logger.info("%s call to %s", method, url_to_log)
        new_kwargs = kwargs.copy()
        new_kwargs.update(
            {"auth": self._get_auth(**kwargs), "headers": self._get_headers(**kwargs)}
        )
        request = requests.request(method, url, **new_kwargs)
        request.raise_for_status()
        return request.content

    def _sanitize_url_for_log(self, url):
        return sanitize_url_for_log(url)

    def get(self, **kwargs):
        return self._request("get", **kwargs)

    def post(self, **kwargs):
        return self._request("post", **kwargs)

    def put(self, **kwargs):
        return self._request("put", **kwargs)

    def _get_auth(self, auth=False, **kwargs):
        if auth:
            return auth
        handler = getattr(self, "_get_auth_for_" + self.collection.auth_type, None)
        return handler(**kwargs) if handler else None

    def _get_auth_for_user_pwd(self, **kw):
        if self.collection.username and self.collection.password:
            return self.collection.username, self.collection.password
        return None

    def _get_headers(self, content_type=False, headers=False, **kwargs):
        headers = headers or {}
        result = {
            "Content-Type": content_type or self.collection.content_type,
        }
        handler = getattr(self, "_get_headers_for_" + self.collection.auth_type, None)
        if handler:
            headers.update(handler(**kwargs))
        result.update(headers)
        return result

    def _get_headers_for_api_key(self, **kw):
        return {self.collection.api_key_header: self.collection.api_key}

    def _get_url(self, url=None, url_params=None, **kwargs):
        if not url:
            # TODO: if url is given, we should validate the domain
            # to avoid abusing a webservice backend for different calls.
            url = self.collection.url
        url_params = url_params or kwargs
        return url.format(**url_params)
