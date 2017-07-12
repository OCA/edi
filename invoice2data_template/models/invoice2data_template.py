# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import cgi
import base64
import logging
import os
import pprint
import sys
from openerp import _, api, fields, models
try:
    from invoice2data.utils import ordered_load
    from invoice2data.template import InvoiceTemplate
    from invoice2data.in_pdftotext import to_text
except ImportError:
    logging.error('Failed to import invoice2data')


def _fork_stdin(stdin, func):
    """fork and call func in the child process, writing stdin to child's fd"""
    read_stdin, write_stdin = os.pipe()
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if not child_pid:
        sys.stdin.close()
        os.dup2(read_stdin, 0)
        os.close(write_stdin)
        os.close(read_fd)
        with os.fdopen(write_fd, 'w') as f:
            f.write(func())
    else:
        os.close(write_fd)
        with os.fdopen(write_stdin, 'w') as f:
            f.write(stdin)
        os.waitpid(child_pid, 0)
        with os.fdopen(read_fd, 'r') as f:
            return f.read()


class Invoice2dataTemplate(models.Model):
    _name = 'invoice2data.template'
    _description = 'Template for invoice2data'

    name = fields.Char(required=True)
    template_type = fields.Selection([], 'Type', required=True)
    template = fields.Text(required=True)
    preview = fields.Html()
    preview_file = fields.Binary('File')
    preview_text = fields.Html(readonly=True)

    @api.multi
    def action_preview(self):
        self.ensure_one()
        if not self.preview_file:
            self.preview = '<div class="oe_error">%s</div>' % _(
                'No PDF file to preview template!'
            )
            return
        else:
            self.preview_text = '<pre>%s</pre>' % cgi.escape(
                _fork_stdin(base64.b64decode(self.preview_file),
                            lambda: to_text('-')) or ''
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
        return '<pre>%s</pre>' % cgi.escape(pprint.pformat(preview_dict))

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
