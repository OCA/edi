# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    def _wamas_export(self, specific_dict=None, telegram_type=False):
        """
        Export the packaging data as WAMAS format

        :return: packaging data as WAMAS format
        :rtype: bytes
        """
        self.ensure_one()
        if not telegram_type:
            raise ValueError(_("Please define expected telegram type."))
        # If having a specific dict for the packaging, we use it
        if specific_dict and isinstance(specific_dict, dict):
            dict_packaging = specific_dict
        else:
            dict_packaging = self.read()[0]
        return self.env["base.wamas.ubl"].dict2wamas(dict_packaging, telegram_type)
