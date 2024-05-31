# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):

    _inherit = "res.partner"

    def get_active_contract(self, transmit_method, domain=None):
        """Return the active contract for a specific transmit method."""
        self.ensure_one()
        base_domain = [
            ("is_valid", "=", True),
            ("partner_id", "=", self.id),
            ("transmit_method_id", "=", transmit_method.id),
        ]
        contract = self.env["ebill.payment.contract"].search(
            AND([domain or [], base_domain]), limit=1
        )
        if not contract:
            _logger.error(
                "eBill contract for {} on {} not found".format(
                    self.name, transmit_method.name
                )
            )
        return contract
