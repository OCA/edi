# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def get_delivery_partner(self):
        self.ensure_one()
        if (
                not self.dest_address_id and
                self.picking_type_id.warehouse_id.partner_id):
            return self.picking_type_id.warehouse_id.partner_id

        return super().get_delivery_partner()
