# Copyright 2023 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)
URL_BASE = "https://api.scaleway.com/billing/v2alpha1"


class AccountInvoiceDownloadConfig(models.Model):
    _inherit = "account.invoice.download.config"

    backend = fields.Selection(
        selection_add=[("scaleway", "Scaleway")], ondelete={"scaleway": "set null"}
    )
    scaleway_secret_key = fields.Char(string="Scaleway Secret Key")

    def prepare_credentials(self):
        credentials = super().prepare_credentials()
        if self.backend == "scaleway":
            credentials = {"secret_key": self.scaleway_secret_key}
        return credentials

    def credentials_stored(self):
        if self.backend == "scaleway":
            if self.scaleway_secret_key:
                return True
            else:
                raise UserError(_("You must set the Scaleway Secret key."))
        return super().credentials_stored()

    def download(self, credentials, logs):
        if self.backend == "scaleway":
            return self.scaleway_download(credentials, logs)
        return super().download(credentials, logs)

    def _scaleway_invoice_attach_pdf(self, parsed_inv, invoice_id, headers):
        logger.info(
            "Starting to download PDF of Scaleway invoice %s dated %s",
            parsed_inv["invoice_number"],
            parsed_inv["date"],
        )
        pdf_invoice_url = "%s/invoices/%s/download" % (URL_BASE, invoice_id)
        logger.debug("Scaleway invoice download url: %s", pdf_invoice_url)
        rpdf = requests.get(pdf_invoice_url, headers=headers)
        logger.info("Scaleway invoice PDF download HTTP code: %s", rpdf.status_code)
        if rpdf.status_code == 200:
            rpdf_json = rpdf.json()
            logger.info(
                "Successfull download of the PDF of the Scaleway invoice %s",
                parsed_inv["invoice_number"],
            )
            filename = rpdf_json["name"]
            parsed_inv["attachments"] = {filename: rpdf_json["content"]}
        else:
            logger.warning(
                "Could not download the PDF of the Scaleway invoice %s. HTTP error %d",
                parsed_inv["invoice_number"],
                rpdf.status_code,
            )

    def scaleway_download(self, credentials, logs):
        invoices = []
        logger.info("Start to download Scaleway invoices with config %s", self.name)
        headers = {
            "Content-type": "application/json",
            "X-Auth-Token": credentials["secret_key"],
        }
        params = {"page_size": 50}
        if self.download_start_date:
            params["started_after"] = "%sT00:00:00Z" % self.download_start_date
        list_url = "%s/invoices" % URL_BASE
        logger.info("Starting Scaleway API query on %s", list_url)
        logger.debug("URL params=%s", params)
        try:
            res_ilist = requests.get(list_url, headers=headers, params=params)
        except Exception as e:
            logs["msg"].append(
                _("Cannot connect to the Scaleway API. Error message: '%s'.") % str(e)
            )
            logs["result"] = "failure"
            return []
        ilist_json = res_ilist.json()
        logger.debug("Result of invoice list: %s", ilist_json)
        for inv in ilist_json.get("invoices", []):
            if not inv.get("number"):
                logger.info(
                    "Skipping scaleway invoice ID %s because it is a draft invoice",
                    inv.get("id"),
                )
                continue
            untaxed = inv["total_untaxed"]
            currency_code = untaxed["currency_code"]
            amount_untaxed_str = "%s.%s" % (untaxed["units"], untaxed["nanos"])
            total = inv["total_taxed"]
            assert total["currency_code"] == currency_code
            amount_total_str = "%s.%s" % (total["units"], total["nanos"])
            parsed_inv = {
                "invoice_number": inv["number"],
                "currency": {"iso": currency_code},
                "date": inv["issued_date"][:10],
                "date_due": inv["due_date"][:10],
                "amount_untaxed": float(amount_untaxed_str),
                "amount_total": float(amount_total_str),
            }
            if inv.get("invoice_type") == "periodic" and inv.get("start_date"):
                start_date_str = inv["start_date"][:10]
                start_date_dt = fields.Date.from_string(start_date_str)
                end_date_dt = start_date_dt + relativedelta(months=1, days=-1)
                parsed_inv.update(
                    {
                        "date_start": start_date_dt,
                        "date_end": end_date_dt,
                    }
                )
            self._scaleway_invoice_attach_pdf(parsed_inv, inv["id"], headers)

            logger.debug("Final parsed_inv=%s", parsed_inv)
            invoices.append(parsed_inv)
        return invoices
