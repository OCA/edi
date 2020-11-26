# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    def _generate_output(self, exchange_record, **kw):
        # Template take precedence over component lookup
        tmpl = self._get_output_template(exchange_record)
        if tmpl:
            return tmpl.generate_output(exchange_record, **kw)
        return super()._generate_output(exchange_record, **kw)

    @property
    def output_template_model(self):
        return self.env["edi.exchange.template.output"]

    def _get_output_template(self, exchange_record, code=None):
        """Retrieve output templates by convention.

        Template's code must match the same component usage as per normal components.
        """
        # TODO: maybe we can add a m2o to output templates
        # but then we would need another for input templates if they are introduced.
        tmpl = None
        candidates = self._generate_output_component_usage_candidates(exchange_record)
        if code:
            candidates.insert(code)
        for usage in candidates:
            tmpl = self.output_template_model.search([("code", "=", usage)], limit=1)
            if tmpl:
                break
        return tmpl
