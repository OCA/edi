# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceDownloadLog(models.Model):
    _name = "account.invoice.download.log"
    _description = "Logs for the download of Supplier Invoices"
    _order = "id desc"
    _rec_name = "create_date"

    download_config_id = fields.Many2one(
        "account.invoice.download.config", string="Download Config", readonly=True
    )
    import_config_id = fields.Many2one(
        related="download_config_id.import_config_id", store=True
    )
    partner_id = fields.Many2one(
        related="download_config_id.import_config_id.partner_id", store=True
    )
    company_id = fields.Many2one(
        "res.company", related="download_config_id.company_id", store=True
    )
    message = fields.Text(string="Message", readonly=True)
    result = fields.Selection(
        [
            ("success", "Success"),
            ("failure", "Failure"),
        ],
        string="Result",
        readonly=True,
    )
    invoice_count = fields.Integer(
        string="Number of Invoices Downloaded", readonly=True
    )
