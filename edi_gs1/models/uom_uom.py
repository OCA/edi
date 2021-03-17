# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    gs1_code = fields.Char(
        string="GS1 code", help="Code used to export with GS1 format"
    )

    @api.model
    def _gs1_mapping_code(self):
        """
        Get a dict with the mapping between the UoM code (from Odoo) and the GS1 code.
        This mapping table is used into the init_hook of the module to automatically
        init existing UoM.
        key should be always in lower case!
        Codes come from this url:
        https://resources.gs1us.org/GS1-US-Data-Hub-Help-Center/ArtMID/3451/
        ArticleID/116/Unit-of-Measure-Codes
        :return: dict
        """
        map_code = {
            "kg": "KGM",
            "day": "DAY",
            "days": "DAY",
            "box": "BX",
            "boxes": "BX",
            "dozen": "DZN",
            "dozens": "DZN",
            "hours": "HUR",
            "hour": "HUR",
            "liters": "LTR",
            "liter": "LTR",
            "cm": "CMT",
            "fl oz": "OZI",
            "foot(ft)": "FOT",
            "foot": "FOT",
            "g": "GRM",
            "gal": "GLI",
            "gals": "GLI",
            "inches": "INH",
            "km": "KMT",
            "m": "MTR",
        }
        return map_code

    @api.model
    def _execute_gs1_map_code(self, overwrite_existing=False):
        """
        Execute (or update) the gs1 mapping based on UoM name (lower case).
        By default, it doesn't update UoM with a value into gs1_code.
        But it can be forced by setting the overwrite_existing parameter to True.
        :param overwrite_existing: bool
        :return: bool
        """
        domain = [("gs1_code", "=", False)]
        if overwrite_existing:
            domain = []
        uoms = self.env["uom.uom"].search(domain)
        map_code = uoms._gs1_mapping_code()
        for uom in uoms:
            # Key always in lower case so the name too!
            name = uom.name.lower()
            gs1_code = map_code.get(name)
            if gs1_code and uom.gs1_code != gs1_code:
                uom.write({"gs1_code": gs1_code})
        return True
