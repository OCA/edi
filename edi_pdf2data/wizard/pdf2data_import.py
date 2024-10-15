# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Pdf2dataImport(models.TransientModel):
    _name = "pdf2data.import"
    _description = "Wizard to import pdf and extract data"

    pdf_file = fields.Binary(string="PDF", required=True)
    pdf_file_name = fields.Char()
    backend_id = fields.Many2one(
        "edi.backend", default=lambda r: r._default_backend(), required=True
    )

    @api.model
    def _default_backend(self):
        return self.env.ref("edi_pdf2data.pdf2data_backend").id

    def import_pdf(self):
        exchange_record = self.backend_id.create_record(
            "pdf2data_generic", self._get_exchange_record_vals()
        )
        self.backend_id.with_context(_edi_receive_break_on_error=True).exchange_process(
            exchange_record
        )
        if exchange_record.model and exchange_record.res_id:
            return exchange_record.record.get_formview_action()
        raise ValidationError(_("No templates found for this document"))

    def _get_exchange_record_vals(self):
        return {
            "edi_exchange_state": "input_received",
            "exchange_file": self.pdf_file,
            "exchange_filename": self.pdf_file_name,
        }
