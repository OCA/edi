# Copyright 2018-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    download_config_ids = fields.One2many(
        "account.invoice.download.config",
        "partner_id",
        string="Download Configurations",
    )
    download_config_count = fields.Integer(
        compute="_compute_download_config_count",
        groups="account.group_account_invoice,account.group_account_readonly",
    )

    @api.depends("download_config_ids")
    def _compute_download_config_count(self):
        rg_res = self.env["account.invoice.download.config"].read_group(
            [("partner_id", "in", self.ids), ("company_id", "=", self.env.company.id)],
            ["partner_id"],
            ["partner_id"],
        )
        mapped_data = {x["partner_id"][0]: x["partner_id_count"] for x in rg_res}
        for partner in self:
            partner.download_config_count = mapped_data.get(partner.id, 0)

    def jump_to_download_config(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account_invoice_download.account_invoice_download_config_action"
        )
        action["context"] = {"default_partner_id": self.id}
        download_configs = self.env["account.invoice.download.config"].search(
            [("partner_id", "=", self.id)]
        )
        if len(download_configs) == 1:
            action.update(
                {
                    "views": False,
                    "view_id": False,
                    "res_id": download_configs.id,
                    "view_mode": "form,list",
                }
            )
        else:
            action["domain"] = [("id", "in", download_configs.ids)]
        return action
