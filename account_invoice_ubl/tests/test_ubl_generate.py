# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger

from ..hooks import (
    remove_ubl_xml_format_in_pdf_invoice,
    set_xml_format_in_pdf_invoice_to_ubl,
)
from .common import TestUblInvoiceMixin

MUTE_LOGGER = "odoo.addons.account_invoice_ubl.models.account_move"

# Use http case to make PDF rendering work


@tagged("-at_install", "post_install")
class TestUblInvoice(HttpCase, TestUblInvoiceMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    # Reduce log noise on CI while rendering GET assets
    @mute_logger("werkzeug")
    def test_ubl_generate(self):
        invoice = self._create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != "ubl":
            invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        for version in ["2.0", "2.1"]:
            pdf_file = (
                self.env["ir.actions.report"]
                .with_context(ubl_version=version, force_report_rendering=True)
                ._render_qweb_pdf("account.report_invoice_with_payments", invoice.ids)[
                    0
                ]
            )
            res = self.env["pdf.helper"].pdf_get_xml_files(pdf_file)
            invoice_filename = invoice.get_ubl_filename(version=version)
            self.assertTrue(invoice_filename in res)

    @mute_logger("werkzeug")
    def test_attach_ubl_xml_file_button(self):
        invoice = self._create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != "ubl":
            invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        self.assertFalse(invoice.company_id.embed_pdf_in_ubl_xml_invoice)
        with mute_logger(MUTE_LOGGER):
            action = invoice.attach_ubl_xml_file_button()
        self.assertEqual(action["res_model"], "ir.attachment")
        self.assertEqual(action["view_mode"], "form,tree")
        self.assertFalse(action["views"])
        invoice.company_id.embed_pdf_in_ubl_xml_invoice = True
        with mute_logger(MUTE_LOGGER):
            action = invoice.attach_ubl_xml_file_button()
        self.assertEqual(action["res_model"], "ir.attachment")
        self.assertEqual(action["view_mode"], "form,tree")
        self.assertFalse(action["views"])

    def test_install_uninstall_hooks(self):
        set_xml_format_in_pdf_invoice_to_ubl(self.env.cr, None)
        self.assertTrue(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
        remove_ubl_xml_format_in_pdf_invoice(self.env.cr, None)
        self.assertFalse(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
        set_xml_format_in_pdf_invoice_to_ubl(self.env.cr, None)
        self.assertTrue(
            self.env["res.company"].search([("xml_format_in_pdf_invoice", "=", "ubl")])
        )
