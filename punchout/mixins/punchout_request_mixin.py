# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PunchoutRequest(models.AbstractModel):
    _name = "punchout.request.mixin"
    _description = "Punchout Request (mixin)"

    @api.model
    def _redirect_to_punchout(self):
        self._check_access_punchout()
        return self.env["punchout.request"]._redirect_to_punchout()

    def _check_access_punchout(self):
        """
        Inherit this method to check if current user can access
        the punchout website depending on the linked model
        """
        return True
