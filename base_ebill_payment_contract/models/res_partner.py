# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_active_contract(self, transmit_method, domain=None):
        """Return the active contract for a specific transmit method."""
        self.ensure_one()
        base_domain = (
            Domain("is_valid", "=", True)
            & Domain("partner_id", "=", self.id)
            & Domain("transmit_method_id", "=", transmit_method.id)
        )
        contract = self.env["ebill.payment.contract"].search(
            Domain(domain or Domain.TRUE) & base_domain, limit=1
        )
        if not contract:
            _logger.error(
                f"eBill contract for {self.name} on {transmit_method.name} not found"
            )
        return contract
