# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import cgi
import json
import logging
import os
import pkg_resources
import pprint

from openerp import _, api, fields, models
from tempfile import mkstemp

try:
    from invoice2data.in_pdftotext import to_text
    from invoice2data.main import extract_data
    from invoice2data.template import InvoiceTemplate
    from invoice2data.template import read_templates
    from invoice2data.utils import ordered_load
except ImportError:
    logging.error('Failed to import invoice2data')


class Invoice2dataTemplate(models.Model):
    _name = 'invoice2data.template'
    _description = 'Template for invoice2data'

    name = fields.Char(required=True)
    template_type = fields.Selection([('purchase_invoice', 'Purchase Invoice')], 'Type',
                                     required=False)
    template = fields.Text(required=True)
    preview = fields.Html()
    preview_file = fields.Binary('File')
    preview_text = fields.Html(readonly=True)
    test_results = fields.Text(readonly=True)

    @api.multi
    def action_preview(self):
        """
        Preview the pdf template as text
        """
        self.ensure_one()
        if not self.preview_file:
            self.preview = '<div class="oe_error">%s</div>' % _(
                'No PDF file to preview template!'
            )
            return
        else:
            fd, file_name = mkstemp()
            try:
                os.write(fd, base64.b64decode(self.preview_file))
            finally:
                os.close(fd)

            self.preview_text = '<pre>%s</pre>' % cgi.escape(
                to_text(file_name))

        if hasattr(self, '_preview_%s' % self.template_type):
            preview = getattr(self, '_preview_%s' % self.template_type)()
            if preview:
                self.preview = preview
            else:
                self.preview = '<div class="oe_error">%s</div>' % _(
                    'Something seems to be wrong with your template!'
                )
        else:
            self.preview = '<div class="oe_error">%s</div>' % _(
                'Previews not available for this kind of template!'
            )

    @api.multi
    def action_test(self):
        """
        Run an import simulation to validate the params for this template
        """
        self.ensure_one()
        if not self.preview_file:
            self.preview = '<div class="oe_error">%s</div>' % _(
                'No PDF file to preview template!'
            )
            return
        else:
            fd, file_name = mkstemp()
            try:
                os.write(fd, base64.b64decode(self.preview_file))
            finally:
                os.close(fd)

            templates = []
            templates += read_templates(
                pkg_resources.resource_filename('invoice2data', 'templates'))
            templates += self.get_template()
            test_results = ''
            invoice2data_res = False

            try:
                invoice2data_res = extract_data(file_name, templates=templates)
            except Exception, e:
                test_results += (_(
                    "PDF Invoice parsing failed. Error message: \n%s\n") % e)
            if not invoice2data_res:
                test_results += (_(
                    "This PDF invoice doesn't match a known template of "
                    "the invoice2data lib.\n"))
            else:
                if invoice2data_res.get('date'):
                    invoice2data_res['date'] = (invoice2data_res['date'].
                                                strftime("%Y-%m-%d"))
                result = json.dumps(invoice2data_res, indent=4,
                                    sort_keys=True)
                test_results += 'Result of invoice2data PDF extraction: \n'
                test_results += result
                needed_keys = ['amount', 'amount_untaxed', 'currency', 'date',
                               'desc', 'invoice_number', 'partner_name']

                for key in needed_keys:
                    if not invoice2data_res.get(key):
                        test_results += _('\n %s is missing' % key)

            self.test_results = test_results

    @api.model
    def _dict2html(self, preview_dict):
        """
        Pretty print a dictionary for HTML output
        """
        return '<pre>%s</pre>' % cgi.escape(pprint.pformat(preview_dict))

    @api.model
    def get_templates(self, template_type):
        """
        Get the templates for a specific template type
        """
        return self.search([
            ('template_type', '=', template_type),
        ]).get_template()

    @api.multi
    def get_template(self):
        """
        Return the template as an array to use by the import
        """
        result = []
        for this in self:
            template = ordered_load(this.template)
            template['template_name'] = this.name
            result.append(InvoiceTemplate(template))
        return result
