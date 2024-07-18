# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiConfiguration(models.Model):
    _inherit = "edi.configuration"

    trigger = fields.Selection(
        selection_add=[
            ("on_button_confirm_purchase_order", "On Button Confirm Purchase Order"),
            ("send_via_email_rfq", "Send via Email RFQ"),
        ],
    )
