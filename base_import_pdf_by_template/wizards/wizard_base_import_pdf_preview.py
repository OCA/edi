# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WizardBaseImportPdfPreview(models.TransientModel):
    _name = "wizard.base.import.pdf.preview"
    _description = "Wizard Base Import Pdf Preview"
    _inherit = "wizard.base.import.pdf.mixin"

    data_file = fields.Binary(string="File", attachment=True)
    file_name = fields.Char(store=True)
    data = fields.Text(string="RAW data", readonly=True)
    total_pages = fields.Integer(string="Total pages", readonly=True)
    template_id = fields.Many2one(
        comodel_name="base.import.pdf.template", readonly=True
    )
    extraction_mode = fields.Selection(
        selection=[("pypdf", "Pypdf")],
        default="pypdf",
        string="Extraction mode",
    )
    header_values = fields.Text(string="Header values", readonly=True)
    table_info = fields.Text(string="Table info", readonly=True)
    lines_values = fields.Text(string="Lines values", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get("active_model") == "base.import.pdf.template":
            res["template_id"] = self.env.context.get("active_id")
        return res

    @api.onchange("data_file", "extraction_mode")
    def _onchange_attachment_ids(self):
        text = False
        total_pages = 0
        if self.data_file:
            data = self._parse_pdf(self.data_file)
            total_pages = len(data)
            text = "".join(data)
        self.data = text
        self.total_pages = total_pages
        # Set header_values, table_info and lines_values
        header_values = False
        table_info = False
        lines_values = False
        if text and self.template_id:
            header_values = self.template_id._get_field_header_values(text)
            table_info = self.template_id._get_table_info(text)
            lines_values = self.template_id._get_field_child_values(table_info)
        self.header_values = header_values
        self.table_info = table_info
        self.lines_values = lines_values
