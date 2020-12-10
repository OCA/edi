# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseWebServiceAdapter(AbstractComponent):
    _name = "base.webservice.adapter"
    _collection = "webservice.backend"
    _webservice_protocol = False
    _usage = "webservice.request"

    @classmethod
    def _component_match(cls, work, usage=None, model_name=None, **kw):
        """Override to customize match.
        Registry lookup filtered by usage and model_name when landing here.
        Now, narrow match to `_match_attrs` attributes.
        """
        return kw.get("webservice_protocol") in (None, cls._webservice_protocol)
