# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase, tagged
from odoo.tools import mute_logger

from ..hooks import (
    remove_ubl_xml_format_in_pdf_invoice,
    set_xml_format_in_pdf_invoice_to_ubl,
)

MUTE_LOGGER = "odoo.addons.account_invoice_ubl.models.account_move"


@tagged("-at_install", "post_install")
class TestUblInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_only_create_invoice(
        self, product=False, qty=1, price=12.42, discount=0, validate=True
    ):
        aio = self.env["account.move"]
        ato = self.env["account.tax"]
        company = self.env.ref("base.main_company")
        taxes = ato.search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "sale"),
                ("unece_type_id", "!=", False),
                ("unece_categ_id", "!=", False),
                ("amount_type", "=", "percent"),
            ]
        )
        if taxes:
            tax = taxes[0]
        else:
            unece_type_id = self.env.ref("account_tax_unece.tax_type_vat").id
            unece_categ_id = self.env.ref("account_tax_unece.tax_categ_s").id
            tax = ato.create(
                {
                    "name": u"German VAT purchase 18.0%",
                    "description": "DE-VAT-sale-18.0",
                    "company_id": company.id,
                    "type_tax_use": "sale",
                    "price_include": False,
                    "amount": 18,
                    "amount_type": "percent",
                    "unece_type_id": unece_type_id,
                    "unece_categ_id": unece_categ_id,
                }
            )
        # validate invoice
        if not product:
            product = self.env.ref("product.product_product_4")
        invoice = aio.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "currency_id": self.env.ref("base.EUR").id,
                "move_type": "out_invoice",
                "company_id": company.id,
                "name": "SO1242",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "quantity": qty,
                            "price_unit": price,
                            "discount": discount,
                            "name": product.name,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )
        if validate:
            invoice.action_post()
        return invoice

    def test_ubl_generate(self):
        invoice = self.test_only_create_invoice()
        if invoice.company_id.xml_format_in_pdf_invoice != "ubl":
            invoice.company_id.xml_format_in_pdf_invoice = "ubl"
        for version in ["2.0", "2.1"]:
            pdf_file = (
                self.env.ref("account.account_invoices")
                .with_context(ubl_version=version, force_report_rendering=True)
                ._render_qweb_pdf(invoice.ids)[0]
            )
            res = self.env["base.ubl"].get_xml_files_from_pdf(pdf_file)
            invoice_filename = invoice.get_ubl_filename(version=version)
            self.assertTrue(invoice_filename in res)

    def test_attach_ubl_xml_file_button(self):
        invoice = self.test_only_create_invoice()
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
