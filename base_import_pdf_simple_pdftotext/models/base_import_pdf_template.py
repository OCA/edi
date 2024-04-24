# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseImportPdfTemplate(models.Model):
    _inherit = "base.import.pdf.template"

    extraction_mode = fields.Selection(
        selection_add=[
            ("pdftotext_lib", "Pdftotext Lib"),
        ],
        ondelete={
            "pdftotext_lib": "cascade",
        },
    )
