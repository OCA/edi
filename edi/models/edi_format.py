# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiFormat(models.Model):
    _name = "edi.format"
    _description = "Electronic Document Format"
    _inherit = "collection.base"

    name = fields.Char(required=True)
    usage = fields.Char()
    active = fields.Boolean(default=True)
    res_model = fields.Char()
    can_receive = fields.Boolean()
    can_send = fields.Boolean()

    def _generate_document(self, record):
        """This function generates a document of this format using record as base"""
        self.ensure_one()
        with self.work_on(record._name) as work:
            document = work.component(usage=self.usage).generate(record)
        return document

    def _send(self, document):
        """Send EDI document (if required), it must return
        True if processed properly, False otherwise"""
        self.ensure_one()
        with self.work_on(document.res_model) as work:
            result = work.component(usage=self.usage).send(document)
        return result

    def _process_document(self, document):
        """This will generate a record from a received document"""
        self.ensure_one()
        with self.work_on(document.res_model) as work:
            result = work.component(usage=self.usage).receive(document)
        return result
