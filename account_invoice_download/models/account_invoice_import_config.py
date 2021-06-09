# Copyright 2018-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceImportConfig(models.Model):
    _inherit = "account.invoice.import.config"

    download_config_ids = fields.One2many(
        "account.invoice.download.config",
        "import_config_id",
        string="Download Configurations",
    )
    download_config_count = fields.Integer(compute="_compute_download_config_count")

    @api.depends("download_config_ids")
    def _compute_download_config_count(self):
        rg_res = self.env["account.invoice.download.config"].read_group(
            [("import_config_id", "in", self.ids)],
            ["import_config_id"],
            ["import_config_id"],
        )
        mapped_data = {
            x["import_config_id"][0]: x["import_config_id_count"] for x in rg_res
        }
        for config in self:
            config.download_config_count = mapped_data.get(config.id, 0)
