# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EdiDocumentMixin(models.AbstractModel):
    _name = "edi.document.mixin"
    _description = "Electronic Document Mixin"

    edi_document_ids = fields.One2many(
        "edi.document",
        inverse_name="res_id",
        domain=lambda r: [("res_model", "=", r._name)],
    )
    edi_document_count = fields.Integer(compute="_compute_edi_document_count",)
    missing_edi_documents = fields.Boolean(
        compute="_compute_missing_documents",
        help="This flag shows when the record needs to generate some documents",
    )

    @api.depends("edi_document_ids")
    def _compute_edi_document_count(self):
        for record in self:
            record.edi_document_count = len(record.edi_document_ids)

    def _expected_edi_documents(self):
        return self.env["edi.format"]

    def _compute_missing_document_record(self):
        """This can be overridden"""
        expected = self._expected_edi_documents()
        return expected and expected not in self.edi_document_ids.mapped(
            "edi_format_id"
        )

    def generate_missing_edi_documents(self):
        documents = self.env["edi.document"]
        for edi_format in self._expected_edi_documents():
            documents |= edi_format._generate_document(self)
        action = self.action_edi_documents()
        action["domain"] = [("id", "in", documents.ids)]
        return action

    def _compute_missing_documents(self):
        for record in self:
            record.missing_edi_documents = record._compute_missing_document_record()

    def action_edi_documents(self):
        self.ensure_one()
        action = self.env.ref("edi.edi_document_act_window").read()[0]
        action["domain"] = [("res_model", "=", self._name), ("res_id", "=", self.id)]
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.id,
        }
        return action

    def get_edi_mail_file_action(self):
        """Override this function to define the action"""
        pass

    def _get_edi_mail_file(self):
        action = self.get_edi_mail_file_action()
        content, content_type = action.render(self.ids)
        mimetype = False
        if content_type == "pdf":
            mimetype = "application/pdf"
        if content_type == "xls":
            mimetype = "application/vnd.ms-excel"
        if content_type == "xlsx":
            mimetype = (
                "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
            )
        if content_type == "csv":
            mimetype = "text/csv"
        if content_type == "xml":
            mimetype = "application/xml"
        return content, self.display_name, mimetype, content_type

    def _update_send_mail_composer(self, composer, document):
        """Hook for changes on mail"""
        pass

    def _send_edi_mail_wizard(self):
        """Action of the mail wizard, to be overridden"""
        pass
