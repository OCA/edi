# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    inventory_ubl_alert_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Alert Recipient",
        required=True,
        default=lambda s: s.env.user.partner_id,
        help="Partner to alert in case of fails on import",
    )
    inventory_ubl_store_document = fields.Boolean(
        string="Store Imported File", help="Import xml file as ERP attachment"
    )
    inventory_ubl_link_document = fields.Boolean(
        string="Link File to Supplier",
        help="If checked, imported attachment is linked to supplier",
    )
