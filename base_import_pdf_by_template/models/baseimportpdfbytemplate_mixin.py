# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BaseimportpdfbytemplatetMixin(models.AbstractModel):
    _name = "baseimportpdfbytemplate.mixin"
    _description = "Functions for baseimportpdfbytemplate mixin documents"

    def _import_record_base_import_pdf_by_template(self, record, attachment):
        """Generic method that will import the attachment of an existing record."""
        wizard = self.env["wizard.base.import.pdf.upload"].create(
            {
                "model": record._name,
                "record_ref": f"{record._name},{record.id}",
                "attachment_ids": [(6, 0, attachment.ids)],
            }
        )
        return wizard.action_process()
