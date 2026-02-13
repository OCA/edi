# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    def _exchange_generate(self, exchange_record, **kw):
        # Template take precedence over component lookup
        tmpl = self._get_template(exchange_record, "output", "generate")
        if tmpl:
            return tmpl.exchange_generate(exchange_record, **kw)
        return super()._exchange_generate(exchange_record, **kw)

    def _exchange_process(self, exchange_record, **kw):
        tmpl = self._get_template(exchange_record, "input", "process")
        if tmpl:
            return tmpl.process_input(exchange_record, **kw)
        return super()._exchange_process(exchange_record, **kw)

    def _get_template(self, exchange_record, direction, action, code=None):
        """Retrieve output templates by convention.

        Template's code must match the same component usage as per normal components.
        """
        search = self.env["edi.exchange.template." + direction].search
        # TODO: maybe we can add a m2o to output templates
        # but then we would need another for input templates if they are introduced.
        tmpl = None
        if code:
            domain = [("code", "=", code)]
            return search(domain, limit=1)
        for domain in self._get_output_template_domains(exchange_record):
            tmpl = search(domain, limit=1)
            if tmpl:
                break
        return tmpl

    def _get_output_template_domains(self, exchange_record):
        """Retrieve domains to lookup for templates by priority."""
        backend_type_leaf = [("backend_type_id", "=", self.backend_type_id.id)]
        exchange_type_leaf = [("type_id", "=", exchange_record.type_id.id)]
        full_match_domain = backend_type_leaf + exchange_type_leaf
        partial_match_domain = backend_type_leaf
        return full_match_domain, partial_match_domain
