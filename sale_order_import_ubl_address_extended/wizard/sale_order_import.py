# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.tools import street_split


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    def _create_missing_partner_vals_cleanup(self, vals: dict) -> dict:
        # OVERRIDE: handle ``street``, ``street_name``, ``street_number`` and
        # ``street_number2`` fields.
        # Module ``base_ubl_parse`` will add fields ``street`` and ``street_number`` to
        # the partner values; however, if the module ``base_address_extended`` is
        # installed, Odoo will call ``res.partner._inverse_street_data()`` after the
        # partner is created, because that method is declared as inverse method of
        # ``street_number``, and it will recompute the ``street`` field value base on
        # ``street_name``, ``street_number`` and ``street_number2``.
        # However, since ``street_name`` is missing at this point, the ``street`` field
        # will simply be cleared completely.
        # To avoid this issue, we try to parse the ``street`` field using Odoo tools'
        # ``split_street()`` function, and update the values accordingly.
        values = super()._create_missing_partner_vals_cleanup(vals)
        if street := values.get("street"):
            street_data = street_split(street)
            # Street name => if ``street_split()`` is unable to parse the street,
            # use the original street value
            values["street_name"] = street_data["street_name"] or street
            # Street number => don't override existing value, if any; else, use the
            # parsed value if possible
            values.setdefault("street_number", street_data["street_number"] or "")
            # Street number 2 => try to retrieve it from the street data
            values["street_number2"] = street_data["street_number2"] or ""
        return values
