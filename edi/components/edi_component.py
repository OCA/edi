# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class EdiFormatConnector(AbstractComponent):
    """ Base exporter for the Bus """

    _name = "edi.format.connector"
    _collection = "edi.format"
    _usage = False
    _apply_on = False

    def receive(self, document):
        """
        We are going to process an EDI Document and try to link it with some record
        """
        self.collection.ensure_one()
        document.ensure_one()
        if not self.collection.can_receive:
            return False
        return self._receive(document)

    def _receive(self, document):
        pass

    def _generate_document_vals(self, record):
        return {
            "state": "to_send",
            "edi_format_id": self.collection.id,
            "res_id": record.id,
            "res_model": record._name,
        }

    def generate(self, record):
        """
        We are going to generate an EDI Document from a record
        """
        return self.env["edi.document"].create(self._generate_document_vals(record))

    def send(self, document):
        """
        We are going to process an EDI Document and try to send it
        """
        self.collection.ensure_one()
        document.ensure_one()
        if not self.collection.can_send:
            return False
        return self._send(document)

    def _send(self, document):
        pass
