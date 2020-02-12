# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    supplier_ack_dt = fields.Datetime(
        "Supplier Acknowledgement Date",
        help="Date and time of the acknowledgement by the supplier. "
        "This field is filled by Odoo when processing a "
        "OrderResponse document.",
        index=True,
    )
