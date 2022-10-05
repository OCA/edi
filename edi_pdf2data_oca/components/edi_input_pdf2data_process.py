# Copyright 2021 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiInputPdf2DataProcessAbstract(Component):
    _name = "edi.input.process.pdf2data.abstract"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process"
    _backend_type = "pdf2data"
    _exchange_type = False

    def _pdf2data_template_domain(self):
        return [("exchange_type_id", "=", self.exchange_record.exchange_type_id.id)]

    def process(self):
        _extracted_text, data, template = (
            self.env["pdf2data.template"]
            .search(self._pdf2data_template_domain())
            ._parse_pdf(self.exchange_record.exchange_file)
        )
        if not template:
            return
        self.process_data(data, template)

    def process_data(self, data, template):
        pass


class EdiInputPdf2DataProcess(Component):
    _name = "edi.input.process.pdf2data"
    _inherit = "edi.input.process.pdf2data.abstract"
    _exchange_type = "pdf2data_generic"

    def _pdf2data_template_domain(self):
        return []

    def process_data(self, data, template):
        if template.exchange_type_id.code == self._exchange_type:
            return
        self.exchange_record.exchange_type_id = template.exchange_type_id
        self.component(
            usage=self._usage,
            backend_type=self._backend_type,
            exchange_type=template.exchange_type_id.code,
        ).process_data(data, template)
