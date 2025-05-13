# Copyright 2025 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_new(self, msg_dict, custom_values=None):
        process_pdf_template = custom_values.pop("process_pdf_template", None)
        if process_pdf_template:
            self = self.with_context(process_pdf_template=process_pdf_template)
        return super().message_new(msg_dict, custom_values)

    def _message_post_after_hook(self, new_message, message_values):
        res = super()._message_post_after_hook(new_message, message_values)
        if self.env.context.get("process_pdf_template", False):
            # Process PDF attachments only if they come from an alias with
            # ‘process_pdf_template’ in default values.
            # One record is already created automatically from the mail alias, all
            # other attachments are processed without the ‘record_ref’ key so that a
            # new record is created for each attachment.
            attachments = new_message.attachment_ids.filtered(
                lambda x: x.mimetype == "application/pdf"
            )
            ctx = self.env.context.copy()
            ctx.pop("default_fetchmail_server_id", None)
            ctx["raise_on_error"] = False
            for index, attachment in enumerate(attachments):
                wiz_vals = {
                    "model": self._name,
                    "attachment_ids": [(6, 0, attachment.ids)],
                }
                if index == 0:
                    wiz_vals["record_ref"] = f"{self._name},{self.id}"
                # pylint: disable=W8121
                pdf_upload_wiz = (
                    self.env["wizard.base.import.pdf.upload"]
                    .with_context(ctx)
                    .create(wiz_vals)
                )
                try:
                    pdf_upload_wiz.action_process()
                except (Exception) as err:
                    _logger.error(err)
        return res
