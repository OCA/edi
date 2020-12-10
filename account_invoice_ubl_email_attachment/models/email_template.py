# -*- coding: utf-8 -*
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, models


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    @api.model
    def generate_email_batch(self, template_id, res_ids, fields=None):
        res = super(EmailTemplate, self).generate_email_batch(
            template_id, res_ids, fields=fields)

        if not self.env.context.get('attach_ubl_xml_file'):
            return res

        template = self.browse(template_id)
        invoices = self.env[template.model_id.model].browse(res_ids)

        for invoice in invoices:
            version = invoice.get_ubl_version()
            ubl_filename = invoice.get_ubl_filename(version=version)
            ubl_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.invoice'),
                ('res_id', '=', invoice.id),
                ('datas_fname', '=', ubl_filename)
            ], order='create_date desc', limit=1)
            if not ubl_attachments:
                ubl_attachments = invoice._generate_email_ubl_attachment()
            if len(ubl_attachments) == 1 and template.report_name:
                report_name = self.render_template(
                    template.report_name, template.model, invoice.id)
                ext = '.xml'
                if not report_name.endswith(ext):
                    report_name += ext
                attachments = [(report_name, ubl_attachments.datas)]
            else:
                attachments = [(a.name, a.datas) for a in ubl_attachments]
            res[invoice.id]['attachments'] += attachments
        return res
