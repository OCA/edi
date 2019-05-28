# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        res = super(MailTemplate, self).generate_email(res_ids, fields)
        if not self.env.context.get('attach_ubl_xml_file'):
            return res
        for res_id, template in self.get_email_template(res_ids).items():
            invoice = self.env['account.invoice'].browse(res_id)
            version = invoice.get_ubl_version()
            ubl_filename = invoice.get_ubl_filename(version=version)
            ubl_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.invoice'),
                ('res_id', '=', res_id),
                ('datas_fname', '=', ubl_filename)
            ])
            if not ubl_attachments:
                ubl_attachments = invoice._generate_email_ubl_attachment()
            if len(ubl_attachments) == 1 and template.report_name:
                report_name = self.render_template(
                    template.report_name, template.model, res_id)
                ext = '.xml'
                if not report_name.endswith(ext):
                    report_name += ext
                attachments = [(report_name, ubl_attachments.datas)]
            else:
                attachments = [(a.name, a.datas) for a in ubl_attachments]
            res[res_id]['attachments'] += attachments
        return res
