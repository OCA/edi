# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WamasDocumentField(models.Model):
    _inherit = "wamas.document.field"

    # From XML to WAMAS Document
    xml_path = fields.Text("XML Path")
    xml_default_value = fields.Text("XML Default Value")
    xml_default_func = fields.Text("XML Default Function")

    @api.model
    def get_default_telegram_sequence(self, seq_value=0):
        return seq_value + 1
