# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, exceptions, models

from odoo.addons.edi_party_data_oca.utils import get_party_data_component


class EDIExchangeOutputTemplate(models.Model):
    """Define an output template to generate outgoing records' content."""

    _inherit = "edi.exchange.template.output"

    def _get_render_values(self, exchange_record, **kw):
        values = super()._get_render_values(exchange_record, **kw)
        values["get_party_data"] = self._get_party_data
        return values

    def _get_party_data(self, exchange_record, partner, raise_if_not_found=True):
        """Shortcut to lookup an info provider for parties."""
        provider = get_party_data_component(exchange_record, partner)
        if not provider and raise_if_not_found:
            raise exceptions.UserError(_("No info provider found for party data"))
        return provider.get_party() if provider else None
