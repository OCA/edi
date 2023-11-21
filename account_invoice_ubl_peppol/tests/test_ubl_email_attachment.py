# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpSavepointCase, tagged
from odoo.tools import mute_logger

from odoo.addons.account_invoice_ubl.tests.common import TestUblInvoiceMixin

# Use http case to make PDF rendering work


@tagged("-at_install", "post_install")
class TestAccountInvoiceUblPeppol(HttpSavepointCase, TestUblInvoiceMixin):

    # Reduce log noise on CI while rendering GET assets
    @mute_logger("werkzeug")
    def test_ubl_generate_peppol(self):
        invoice = self._create_invoice()
        invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        version = "2.1"
        report = self.env.ref("account.account_invoices")
        pdf_file = report.with_context(
            ubl_version=version, force_report_rendering=True
        )._render_qweb_pdf(invoice.ids)[0]
        res = self.env["base.ubl"].get_xml_files_from_pdf(pdf_file)
        invoice_filename = invoice.get_ubl_filename(version=version)
        self.assertTrue(invoice_filename in res)
        # TODO: implement PEPPOL validation here
