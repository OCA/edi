# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import logging

from odoo.tests.common import Form

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class EdiFormatConnectorMail(AbstractComponent):
    """ Base exporter for the Bus """

    _name = "edi.format.connector.mail"
    _inherit = "edi.format.connector"
    _usage = "mail"

    def receive(self, document):
        """
        We are going to process an EDI Document and try to link it with some record
        """
        self.collection.ensure_one()
        document.ensure_one()
        if not self.collection.can_receive:
            return False
        return self._receive(document)

    def _generate_document_vals(self, record):
        vals = super()._generate_document_vals(record)
        file, file_name, mimetype, content_type = record._get_edi_mail_file()
        attachment = (
            self.env["ir.attachment"]
            .with_context({})
            .create(
                {
                    "name": file_name,
                    "datas": base64.b64encode(file),
                    "res_model": record._name,
                    "res_id": record.id,
                    "mimetype": mimetype,
                }
            )
        )
        vals["attachment_id"] = attachment.id
        return vals

    def _send(self, document):
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
