# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    invoice_import_ids = fields.One2many(
        "account.invoice.import.config",
        "partner_id",
        string="Invoice Import Configuration",
    )
    invoice_import_count = fields.Integer(
        compute="_compute_invoice_import_count",
        string="Number of Invoice Import Configurations",
        readonly=True,
    )

    def _compute_invoice_import_count(self):
        config_data = self.env["account.invoice.import.config"].read_group(
            [("partner_id", "in", self.ids), ("company_id", "=", self.env.company.id)],
            ["partner_id"],
            ["partner_id"],
        )
        mapped_data = {
            config["partner_id"][0]: config["partner_id_count"]
            for config in config_data
        }
        for partner in self:
            partner.invoice_import_count = mapped_data.get(partner.id, 0)

    def show_account_invoice_import_config(self):
        self.ensure_one()
        xmlid = "account_invoice_import.account_invoice_import_config_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["context"] = {
            "default_name": self.name,
            "default_partner_id": self.id,
            "search_default_partner_id": self.id,
            "invoice_import_config_main_view": True,
        }
        return action
