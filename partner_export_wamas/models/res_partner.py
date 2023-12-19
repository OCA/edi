# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _wamas_export(self, specific_dict=None, telegram=False):
        """
        Export the partner data as WAMAS format

        :return: partner data as WAMAS format
        :rtype: bytes
        """
        self.ensure_one()
        if not telegram:
            raise ValueError(_("Need telegram for exporting"))
        # If having a specific dict for the partner, we use it
        if specific_dict and isinstance(specific_dict, dict):
            dict_partner = specific_dict
        else:
            dict_partner = self.read()[0]
        base_wamas_ubl = self.env["base.wamas.ubl"]
        return base_wamas_ubl.dict2wamas(dict_partner, telegram)
