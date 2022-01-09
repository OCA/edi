# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock
from odoo.tools.misc import mute_logger
from .common import InvoiceDownloadCommon
from odoo.tests.common import SavepointCase
from odoo.exceptions import UserError
from freezegun import freeze_time


class TestInvoiceDownload(InvoiceDownloadCommon, SavepointCase):

    def test_download_config_default_date(self):
        self.assertFalse(self.default_config_line.download_start_date)

    def test_download_config_credentials(self):
        # Test credentials_stored function
        self.assertFalse(self.default_config_line.credentials_stored())
        self.default_config_line.login = "admin"
        self.default_config_line.password = "password"
        self.assertTrue(self.default_config_line.credentials_stored())
        # Test prepare_credentials function
        res = self.default_config_line.prepare_credentials()
        self.assertDictEqual(
            res,
            {"login": "admin", "password": "password"}
        )

    @mute_logger("odoo.addons.account_invoice_download.models."
                 "account_invoice_download_config")
    def test_credentials_wizard_no_backend(self):
        # Test credentials wizard with no values
        with self.assertRaises(UserError):
            self.wizard_obj.create({})

    @mute_logger("odoo.addons.account_invoice_download."
                 "models.account_invoice_download_config")
    def test_credentials_wizard(self):
        # Test credentials wizard
        # Download start should have been updated
        wizard = self.wizard_obj.with_context(
            active_model="account.invoice.download.config",
            active_id=self.default_config_line.id)

        default_vals = wizard.default_get(self.wizard_obj._fields)
        the_wizard = wizard.create(default_vals)

        self.assertTrue(
            self.default_config_line.download_start_date
        )
        res = the_wizard.run()
        model = res.get("res_model")
        self.assertEqual(
            model,
            "account.invoice.download.log",
        )

    def test_download_config_name(self):
        self.assertEqual(
            "Default Partner (False / manual)",
            self.default_config_line.name_get()[0][1])

    @freeze_time("2022-01-01 10:00:00")
    @mute_logger("odoo.addons.account_invoice_download."
                 "models.account_invoice_download_config")
    def test_download_cron(self):
        # Test the cron run
        # Default interval is monthly
        # Check if next_run has been updated
        self.default_config_line.login = "admin"
        self.default_config_line.password = "password"
        self.default_config_line.method = "auto"
        self.default_config_line.next_run = "2021-12-01"
        self.default_config_line.run_cron()
        self.assertEqual(
            self.default_config_line.next_run,
            "2022-02-01"
        )

    def test_download_fake(self):
        # Check the file download will create an invoice
        # Check for the attachment value
        invoices_before = self.account_invoice.search([
            ("type", "=", "in_invoice"),
            ("partner_id", "=", self.partner.id)])
        self.default_config_line.backend = "fake_test"
        self.default_config_line.login = "admin"
        self.default_config_line.password = "password"
        with mock.patch.object(
                self.env["account.invoice.import"].__class__,
                "fallback_parse_pdf_invoice") as parse_mock:
            parse_mock.return_value = self._get_parsed_invoice()
            self.default_config_line.run(
                self.default_config_line.prepare_credentials())
        invoices_after = self.account_invoice.search([
            ("type", "=", "in_invoice"),
            ("partner_id", "=", self.partner.id)]) - invoices_before
        self.assertEqual(
            1,
            len(invoices_after)
        )
        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "account.invoice"),
            ("res_id", "=", invoices_after.id),
            ("name", "=", "Vendor Bill - BILL_2022_0002.pdf")])
        self.assertEqual(
            1,
            len(attachment)
        )
