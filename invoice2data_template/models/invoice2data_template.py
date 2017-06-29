# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import _, api, fields, models
try:
    from invoice2data.utils import ordered_load
    from invoice2data.template import InvoiceTemplate
except ImportError:
    logging.error('Failed to import invoice2data')


class Invoice2dataTemplate(models.Model):
    _name = 'invoice2data.template'
    _description = 'Template for invoice2data'

    name = fields.Char(required=True)
    template_type = fields.Selection([], 'Type', required=True)
    template = fields.Text(required=True)
    preview = fields.Html()
    preview_file = fields.Binary('File')

    @api.multi
    def action_preview(self):
        self.ensure_one()
        if not self.preview_file:
            self.preview = '<div class="oe_error">%s</div>' % _(
                'No PDF file to preview template!'
            )
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

    @api.model
    def _dict2html(self, preview_dict):
        """Pretty print a dictionary for HTML output"""
        return '<pre>%s</pre>' % str(preview_dict).replace('\n', '<br/>')

    @api.model
    def get_templates(self, template_type):
        return self.search([
            ('template_type', '=', template_type),
        ]).get_template()

    @api.multi
    def get_template(self):
        result = []
        for this in self:
            template = ordered_load(this.template)
            template['template_name'] = this.name
            result.append(InvoiceTemplate(template))
        return result
