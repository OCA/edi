# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):

    _inherit = "res.partner"

    def get_active_contract(self, transmit_method):
        """Return the active contract for a specific transmit method."""
        self.ensure_one()
        contracts = self.env["ebill.payment.contract"].search(
            [("is_valid", "=", True), ("partner_id", "=", self.id)],
            limit=1,
        )
        if not contracts:
            _logger.error(
                "Paynet contract for {} on {} not found".format(
                    self.name, transmit_method.name
                )
            )
        return contracts[0] if contracts else contracts
