# Copyright 2021 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiInputPdf2DataProcess(Component):
    _name = "edi.input.process.pdf2data.import_data"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process"
    _backend_type = "import_data"
    _exchange_type = "pdf2data"

    def process(self):
        data, template = (
            self.env["pdf2data.template"]
            .search([])
            ._parse_pdf(self.exchange_record.exchange_file)
        )
        if not template:
            return
        component = self.component(
            usage="process_data",
            backend_type=self.exchange_record.backend_id.backend_type_id.code,
            exchange_type=self.exchange_record.type_id.code,
            process_type=template.type_id.code,
        )
        component.process_data(data, template)
