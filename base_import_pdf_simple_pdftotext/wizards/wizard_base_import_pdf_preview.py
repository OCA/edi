# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WizardBaseImportPdfPreview(models.TransientModel):
    _inherit = "wizard.base.import.pdf.preview"

    extraction_mode = fields.Selection(
        selection_add=[
            ("pdftotext_lib", "Pdftotext Lib"),
        ],
        ondelete={
            "pdftotext_lib": "cascade",
        },
    )
