# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component

CHUNK_GROUP_FIELDS = [
    "job_priority",
    "chunk_size",
    "process_multi",
    "data_format",
    "apply_on_model",
    "usage",
    "xml_split_xpath",
]


class ProcessWithChunk(Component):
    _name = "edi.input.process.with.chunk"
    _inherit = "edi.component.input.mixin"
    _usage = "process.with.chunk"

    def process(self):
        vals = {"edi_exchange_record_id": [(4, self.exchange_record.id, 0)]}
        for key in CHUNK_GROUP_FIELDS:
            if hasattr(self.work, key):
                vals[key] = getattr(self.work, key)
        self.env["chunk.group"].create(vals)
