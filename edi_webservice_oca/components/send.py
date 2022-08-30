# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions

from odoo.addons.component.core import Component


class EDIWebserviceSend(Component):
    """Generic component for webservice requests.

    Configuration is expected to come from the work ctx key `webservice`.
    You can easily pass via exchange type advanced settings.
    """

    _name = "edi.webservice.send"
    _inherit = [
        "edi.component.mixin",
    ]
    _usage = "webservice.send"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.ws_settings = getattr(work_context, "webservice", {})

    def send(self):
        webservice_backend = self.backend.webservice_backend_id
        method, pargs, kwargs = self._get_call_params()
        return webservice_backend.call(method, *pargs, **kwargs)

    def _get_call_params(self):
        try:
            method = self.ws_settings["method"].lower()
        except KeyError as err:
            raise exceptions.UserError(
                _("`method` is required in `webservice` type settings.")
            ) from err
        pargs = self.ws_settings.get("pargs", [])
        kwargs = self.ws_settings.get("kwargs", {})
        kwargs["data"] = self._get_data()
        return method, pargs, kwargs

    def _get_data(self):
        return self.exchange_record._get_file_content()
