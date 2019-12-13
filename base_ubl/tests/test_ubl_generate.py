# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.addons.account_tax_unece.tests.test_account_invoice import TestAccountInvoice


class TestUblInvoice(TestAccountInvoice):
    def test_pdf_generate(self):
        invoice = self.test_only_create_invoice()
        content, doc_type = (
            self.env.ref("account.account_invoices")
            .with_context(no_embedded_ubl_xml=True, force_report_rendering=True)
            .env.ref("account.account_invoices")
            .render_qweb_pdf(invoice.ids)
        )
        self.assertTrue(content)
        self.assertEqual(doc_type, "pdf")

    def test_ubl_generate(self):
        invoice = self.test_only_create_invoice()
        nsmap, ns = self.env["base.ubl"]._ubl_get_nsmap_namespace("Invoice-2")
        xml_root = etree.Element("Invoice", nsmap=nsmap)

        self.env["base.ubl"]._ubl_add_supplier_party(
            False, invoice.company_id, "AccountingSupplierParty", xml_root, ns
        )
        self.env["base.ubl"]._ubl_add_customer_party(
            invoice.partner_id, False, "AccountingCustomerParty", xml_root, ns
        )
