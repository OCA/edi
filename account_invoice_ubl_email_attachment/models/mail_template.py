# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields=None):
        res = super().generate_email(res_ids, fields)

        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        if not self.env.context.get("attach_ubl_xml_file"):
            return res
        for res_id, template in self.get_email_template(res_ids).items():
            invoice = self.env["account.move"].browse(res_id)
            version = invoice.get_ubl_version()
            ubl_filename = invoice.get_ubl_filename(version=version)
            ubl_attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "account.move"),
                    ("res_id", "=", res_id),
                    ("name", "=", ubl_filename),
                ],
                order="create_date desc",
                limit=1,
            )
            if not ubl_attachment:
                ubl_attachment = invoice._generate_email_ubl_attachment()
            if template.report_name:
                report_name = self._render_template(
                    template.report_name, template.model, res_id
                )
                ext = ".xml"
                if not report_name.endswith(ext):
                    report_name += ext
                attachments = [(report_name, ubl_attachment.datas)]
            else:
                attachments = [(ubl_attachment.name, ubl_attachment.datas)]
            res[res_id]["attachments"] += attachments
        return multi_mode and res or res[res_ids[0]]
