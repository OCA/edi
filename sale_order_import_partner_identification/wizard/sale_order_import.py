# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.fields import Command


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    def _create_missing_invoice_partner_values(
        self, invoice_partner_data: dict, partner: models.BaseModel, chatter_msg: list
    ) -> dict:
        # OVERRIDE: set partner's ID numbers when importing a new invoicing partner
        values = super()._create_missing_invoice_partner_values(
            invoice_partner_data, partner, chatter_msg
        )
        values["id_numbers"] = self._create_missing_partner_id_numbers_values(
            invoice_partner_data.get("id_number") or []
        )
        return values

    def _create_missing_shipping_partner_values(
        self, shipping_partner_data: dict, partner: models.BaseModel, chatter_msg: list
    ) -> dict:
        # OVERRIDE: set partner's ID numbers when importing a new shipping partner
        values = super()._create_missing_shipping_partner_values(
            shipping_partner_data, partner, chatter_msg
        )
        values["id_numbers"] = self._create_missing_partner_id_numbers_values(
            shipping_partner_data.get("id_number") or []
        )
        return values

    def _create_missing_partner_id_numbers_values(
        self, parsed_id_numbers: list[dict[str, str]]
    ) -> list[tuple[int, int, dict]]:
        """Converts the parsed ID numbers to X2many commands to create new ID Numbers"""
        values = []
        categ_obj = self.env["res.partner.id_category"]
        for id_number_data in parsed_id_numbers:
            # Check parsed data contains an ID number
            if not (number := id_number_data.get("value")):
                continue
            # Check parsed data contains a category code
            if not (categ_code := id_number_data.get("schemeID")):
                continue
            # Check category code is linked to a category record
            if not (categ := categ_obj.search([("code", "=", categ_code)], limit=1)):
                continue
            # Create the new ID Number record
            values.append(Command.create({"name": number, "category_id": categ.id}))
        return values
