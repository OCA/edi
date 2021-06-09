# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class AccountInvoiceDownloadCredentials(models.TransientModel):
    _name = "account.invoice.download.credentials"
    _description = "Wizard to ask credentials to download invoice"

    download_config_id = fields.Many2one(
        "account.invoice.download.config", "Invoice Download Config", required=True
    )
    backend = fields.Selection(related="download_config_id.backend", readonly=True)
    login = fields.Char()
    password = fields.Char()
    invoice_ids_str = fields.Char(
        help="This field is a technical hack to be able to return "
        "the action with the created invoices"
    )
    log_id = fields.Many2one("account.invoice.download.log", string="Log")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert (
            self._context.get("active_model") == "account.invoice.download.config"
        ), "Wrong active_model"
        assert self._context.get("active_id"), "Missing active_id"
        config = self.env["account.invoice.download.config"].browse(
            self._context["active_id"]
        )
        res.update(
            {
                "download_config_id": config.id,
                "login": config.login,
            }
        )
        return res

    @api.model
    def prepare_and_remove_credentials(self, vals):
        credentials = {
            "login": vals.get("login"),
            "password": vals.get("password"),
        }
        # NEVER store password in Odoo's database !
        if "password" in vals:
            vals.pop("password")
        return credentials

    @api.model
    def create(self, vals):
        credentials = self.prepare_and_remove_credentials(vals)
        if not vals.get("download_config_id"):
            raise UserError(_("Missing Invoice Download Config"))
        download_config = self.env["account.invoice.download.config"].browse(
            vals["download_config_id"]
        )
        invoice_ids, log_id = download_config.run(credentials)
        download_config.last_run = fields.Date.context_today(self)
        vals["log_id"] = log_id
        if invoice_ids:
            vals["invoice_ids_str"] = "[%s]" % ",".join(
                [str(inv_id) for inv_id in invoice_ids]
            )
        return super().create(vals)

    def run(self):
        """The real work is made in create(), not here!"""
        self.ensure_one()
        if self.invoice_ids_str:
            action = (
                self.env.ref("account.action_move_in_invoice_type").sudo().read()[0]
            )
            action.update(
                {
                    "views": False,
                    "view_id": False,
                    "domain": "[('id', 'in', %s)]" % self.invoice_ids_str,
                }
            )
        else:
            action = (
                self.env.ref(
                    "account_invoice_download.account_invoice_download_log_action"
                )
                .sudo()
                .read()[0]
            )
            action.update(
                {
                    "res_id": self.log_id.id,
                    "views": False,
                    "view_mode": "form,tree",
                }
            )
        return action
