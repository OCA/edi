# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_peppol_endpoint_id(self):
        """
        Returns the value of the PEPPOL EndpointID for a partner,
        as well as the SchemeID (EAS) which describes what the value stands for.
        """
        self.ensure_one()
        # Override this function if your business case requires other values.
        return {
            "endpoint_id": self.coc_registration_number,
            "scheme_id": self.country_id.peppol_eas_code.code,
        }
