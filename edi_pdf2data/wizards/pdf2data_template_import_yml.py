# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import yaml

from odoo import fields, models


class Pdf2dataTemplateImportYml(models.TransientModel):

    _name = "pdf2data.template.import.yml"

    template_id = fields.Many2one("pdf2data.template")
    data = fields.Text(required=True)

    def import_data(self):
        self.template_id._import_yml(yaml.safe_load(self.data))
