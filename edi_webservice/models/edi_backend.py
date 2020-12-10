# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiBackend(models.Model):

    _inherit = "edi.backend"

    webservice_backend_id = fields.Many2one("webservice.backend")
    _webservice_actions = ("send", "receive")

    def _get_component_usage_candidates(self, exchange_record, key):
        candidates = super()._get_component_usage_candidates(exchange_record, key)
        if not self.webservice_backend_id or key not in self._webservice_actions:
            return candidates
        return ["webservice.{}".format(key)] + candidates

    def _component_match_attrs(self, exchange_record, key):
        # Override to inject `webservice_protocol` as match attribute
        res = super()._component_match_attrs(exchange_record, key)
        if not self.webservice_backend_id or key not in self._webservice_actions:
            return res
        res["webservice_protocol"] = self.webservice_backend_id.protocol
        return res

    def _component_sort_key(self, component_class):
        res = super()._component_sort_key(component_class)
        # Override to give precedence by `webservice_protocol` when needed.
        if not self.webservice_backend_id:
            return res
        return (
            1 if getattr(component_class, "_webservice_protocol", False) else 0,
        ) + res
