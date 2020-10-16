# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models
from odoo.tests.common import Form


class EdiFormat(models.Model):
    _name = "edi.format"
    _description = "Electronic Document Format"

    name = fields.Char(required=True)
    format_key = fields.Selection(selection=[("mail", "Mail")])
    active = fields.Boolean(default=True)
    usage = fields.Char()
    can_receive = fields.Boolean()
    can_send = fields.Boolean()

    def _generate_document_vals(self, record):
        """This is the base function used to generate the vals"""
        return {
            "state": "to_send",
            "edi_format_id": self.id,
            "res_id": record.id,
            "res_model": record._name,
        }

    def _generate_document(self, record):
        """This function generates a document of this format using record as base"""
        self.ensure_one()
        return getattr(self, "_generate_document_%s" % self.format_key)(record)

    def _send(self, document):
        """Send EDI document (if required), it must return
        True if processed properly, False otherwise"""
        self.ensure_one()
        if not self.can_send:
            return False
        if hasattr(self, "_send_%s" % self.format_key):
            return getattr(self, "_send_%s" % self.format_key)(document)
        return True

    def _process_document(self, document):
        """This will generate a record from a received document"""
        self.ensure_one()
        if not self.can_receive:
            return False
        return getattr(self, "_process_document_%s" % self.format_key)(document)

    def _generate_document_mail_vals(self, record):
        vals = self._generate_document_vals(record)
        invoice_file, file_name, mimetype, content_type = record._get_edi_mail_file()
        attachment = (
            self.env["ir.attachment"]
            .with_context({})
            .create(
                {
                    "name": file_name,
                    "datas": base64.b64encode(invoice_file),
                    "res_model": record._name,
                    "res_id": record.id,
                    "mimetype": mimetype,
                }
            )
        )
        vals["attachment_id"] = attachment.id
        return vals

    def _generate_document_mail(self, record):
        return self.env["edi.document"].create(
            self._generate_document_mail_vals(record)
        )

    def _send_mail(self, document):
        record = self.env[document.res_model].browse(document.res_id)
        wizard = record._send_edi_mail_wizard()
        context = wizard["context"]
        context.update({"edi_document_id": document.id})
        with Form(
            self.env[wizard["res_model"]].with_context(**context)
        ) as composer_form:
            record._update_send_mail_composer(composer_form, document)
            composer = composer_form.save()
            composer.send_mail()
        return True
