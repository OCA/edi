
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import base64
from odoo import fields, models

directory = os.path.dirname(__file__)


class AccountInvoiceDownloadConfigFake(models.Model):
    _name = "account.invoice.download.config"
    _inherit = "account.invoice.download.config"

    backend = fields.Selection(
        selection_add=[("fake_test", "FAKE TEST")]
    )

    def download(self, credentials, logs):
        if self.backend == "fake_test":
            return self.fake_download(credentials, logs)
        return super().download(credentials, logs)

    def fake_download(self, credentials, logs):
        with open(
                os.path.join(
                    directory,
                    "Vendor Bill - BILL_2022_0002.pdf"), "rb") as file_name:
            file_invoice = base64.b64encode(file_name.read())
        return [(file_invoice, "Vendor Bill - BILL_2022_0002.pdf")]
