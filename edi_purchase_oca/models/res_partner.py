# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edi_purchase_conf_ids = fields.Many2many(
        string="EDI Purchase Config Ids",
        comodel_name="edi.configuration",
        relation="res_partner_edi_configuration_rel",
        column1="partner_id",
        column2="conf_id",
        # TODO: Domain for Purchase model
        domain="[('model_name', '=', 'purchase.order')]"
    )
