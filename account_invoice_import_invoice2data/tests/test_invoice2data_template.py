# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import logging

from odoo import fields
from odoo.tests.common import SavepointCase
from odoo.tools import config, file_open, float_compare

try:
    pass
except ImportError:
    logging.error("Failed to import invoice2data")


class TestInvoice2dataTemplate(SavepointCase):
    def setUp(self):
        super(TestInvoice2dataTemplate, self).setUp()
        self.templates = self.env["invoice2data.template"]

    def test_01_invoice2data_template(self):
        """ Test if we cancreate a template. """
        self.assertEqual(0, len(self.templates.get_templates("purchase_invoice")))
        self._create_template()
        self.assertEqual(1, len(self.templates.get_templates("purchase_invoice")))

    def test_02_import_custom_invoice_template(self):
        """ Test if a created template is used to import the pdf invoice. """
        config.__setitem__("invoice2data_exclude_built_in_templates", True)
        # Be sure we exclude built in templates
        self.assertTrue(config.get("invoice2data_exclude_built_in_templates"))

        self._create_template()

        filename = "invoice_free_fiber_201507.pdf"
        f = file_open("account_invoice_import_invoice2data/tests/pdf/" + filename, "rb")
        pdf_file = f.read()
        pdf_file_b64 = base64.b64encode(pdf_file)
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": pdf_file_b64,
                "invoice_filename": filename,
            }
        )
        f.close()
        wiz.import_invoice()
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "562044387"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(inv.move_type, "in_invoice")
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2015-07-05")
        self.assertEqual(
            inv.partner_id, self.env.ref("account_invoice_import_invoice2data.free")
        )
        self.assertEqual(inv.journal_id.type, "purchase")
        self.assertEqual(float_compare(inv.amount_total, 29.99, precision_digits=2), 0)
        self.assertEqual(
            float_compare(inv.amount_untaxed, 24.99, precision_digits=2), 0
        )
        self.assertEqual(len(inv.invoice_line_ids), 1)
        iline = inv.invoice_line_ids[0]
        self.assertEqual(iline.name, "Fiber optic access at the main office")
        self.assertEqual(
            iline.product_id,
            self.env.ref("account_invoice_import_invoice2data.internet_access"),
        )
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 24.99, precision_digits=2), 0)

        # Prepare data for next test i.e. invoice update
        # (we re-use the invoice created by the first import !)
        inv.write(
            {
                "invoice_date": False,
                "ref": False,
            }
        )

        # New import with update of an existing draft invoice
        wiz2 = self.env["account.invoice.import"].create(
            {
                "invoice_file": pdf_file_b64,
                "invoice_filename": "invoice_free_fiber_201507.pdf",
            }
        )
        action = wiz2.import_invoice()
        self.assertEqual(action["res_model"], "account.invoice.import")
        # Choose to update the existing invoice
        wiz2.update_invoice()
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "562044387"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2015-07-05")

    def _create_template(self):
        """ Create a template for free adsl fiber. """
        # Swapped date_due and date for testing purpose, so that this won't
        # map with the built in templates
        self.templates.create(
            {
                "name": "Test template free adsl fiber",
                "template_type": "purchase_invoice",
                "template": "issuer: Free\n"
                + "fields:\n"
                + "  amount: Total facture\\s+\\d+.\\d{2}\\s+\\d+.\\d{2}\\s+(\\d+.\\d{2})\n"
                + "  amount_untaxed: Total facture\\s+(\\d+.\\d{2})\n"
                + "  date_due: Facture n°\\d+ du (\\d+ .+ \\d{4})\n"
                + "  date: Date limite de paiement le (\\d+ .+ \\d{4})\n"
                + "  invoice_number: Facture n°(\\d+)\n"
                + "  static_vat: FR60421938861\n"
                + "keywords:\n"
                + "  - FR 604 219 388 61\n"
                + "  - Facture\n"
                + "  - EUR\n"
                + "tables:\n"
                + "  - start: Numéro de ligne\\s+Id\\.client\\s+Adresse de l’installation\n"
                + "    end: Facture n°\n"
                + "    body: (?P<line_number>\\w+)\\s+(?P<client_id>\\d+)\\s+[\\w ]+\n"
                + "options:\n"
                + "  currency: EUR\n"
                + "  date_formats:\n"
                + "      - '%d %B %Y'\n"
                + "  languages:\n"
                + "    - fr\n"
                + "  decimal_separator: '.'",
            }
        )
