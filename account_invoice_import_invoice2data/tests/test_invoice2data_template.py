# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import logging
from openerp.tests.common import SavepointCase
from openerp.tools import file_open, float_compare, config

try:
    from invoice2data.in_pdftotext import to_text
    from invoice2data.main import extract_data
    from invoice2data.main import loggeri2data
    from invoice2data.template import InvoiceTemplate
    from invoice2data.template import read_templates
    from invoice2data.utils import ordered_load
except ImportError:
    logging.error('Failed to import invoice2data')


class TestInvoice2dataTemplate(SavepointCase):

    def setUp(cls):
        super(TestInvoice2dataTemplate, cls).setUp()
        cls.templates = cls.env['invoice2data.template']

    def test_01_invoice2data_template(self):
        """ Test if we cancreate a template. """
        self.assertEquals(0, len(self.templates.get_templates('purchase_invoice')))
        self._create_template()
        self.assertEquals(1, len(self.templates.get_templates('purchase_invoice')))

    def test_02_import_custom_invoice_template(self):
        """ Test if a created template is used to import the pdf invoice. """
        config.__setitem__('invoice2data_exclude_built_in_templates', True)
        # Be sure we exclude built in templates
        self.assertTrue(config.get('invoice2data_exclude_built_in_templates'))

        self._create_template()

        filename = 'invoice_free_fiber_201507.pdf'
        f = file_open(
            'account_invoice_import_invoice2data/tests/pdf/' + filename, 'rb')
        pdf_file = f.read()
        wiz = self.env['account.invoice.import'].create({
            'invoice_file': base64.b64encode(pdf_file),
            'invoice_filename': filename,
        })
        f.close()
        wiz.import_invoice()
        # Check result of invoice creation
        invoices = self.env['account.invoice'].search([
            ('state', '=', 'draft'),
            ('type', '=', 'in_invoice'),
            ('supplier_invoice_number', '=', '562044387')
            ])
        self.assertEquals(len(invoices), 1)
        inv = invoices[0]
        self.assertEquals(inv.type, 'in_invoice')
        self.assertEquals(inv.date_due, '2015-07-02')
        self.assertEquals(inv.date_invoice, '2015-07-05')
        self.assertEquals(
            inv.partner_id,
            self.env.ref('account_invoice_import_invoice2data.free'))
        self.assertEquals(inv.journal_id.type, 'purchase')
        self.assertEquals(
            float_compare(inv.check_total, 29.99, precision_digits=2), 0)
        self.assertEquals(
            float_compare(inv.amount_total, 29.99, precision_digits=2), 0)

    def _create_template(self):
        """ Create a template for free adsl fiber. """
        # Swapped date_due and date for testing purpose, so that this won't
        # map with the built in templates
        self.templates.create({
            'name': 'Test template free adsl fiber',
            'template_type': 'purchase_invoice',
            'template': "issuer: Free\n" +
            "fields:\n" +
            "  amount: Total facture\s+\d+.\d{2}\s+\d+.\d{2}\s+(\d+.\d{2})\n" +
            "  amount_untaxed: Total facture\s+(\d+.\d{2})\n" +
            "  date_due: Facture n°\d+ du (\d+ .+ \d{4})\n" +
            "  date: Date limite de paiement le (\d+ .+ \d{4})\n" +
            "  invoice_number: Facture n°(\d+)\n" +
            "  static_vat: FR60421938861\n" +
            "keywords:\n" +
            "  - FR 604 219 388 61\n" +
            "  - Facture\n" +
            "  - EUR\n" +
            "tables:\n" +
            "  - start: Numéro de ligne\s+Id\.client\s+Adresse de l’installation\n" +
            "    end: Facture n°\n" +
            "    body: (?P<line_number>\w+)\s+(?P<client_id>\d+)\s+[\w ]+\n" +
            "options:\n" +
            "  currency: EUR\n" +
            "  date_formats:\n" +
            "      - '%d %B %Y'\n" +
            "  languages:\n" +
            "    - fr\n" +
            "  decimal_separator: '.'"
        })
