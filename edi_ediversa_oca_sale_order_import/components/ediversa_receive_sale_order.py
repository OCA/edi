# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EdiversaReceiveSaleOrder(Component):
    _name = "ediversa.receive.sale.order"
    _usage = "input.receive"
    _backend_type = "ediversa"
    _exchange_type = "ediversa_sale_input"
    _inherit = ["edi.component.receive.mixin"]

    def receive(self):
        exchange_record = self.exchange_record
        if not exchange_record.company_id.use_edi_ediversa:
            return
        face = self.env.ref("edi_ediversa_oca.ediversa_backend")
        component = face._find_component(
            face._name,
            ["ediversa.api"],
            work_ctx={"exchange_record": self.env["edi.exchange.record"]},
        )
        doc = component.download_document(
            exchange_record.external_identifier, exchange_record.company_id
        )
        if doc.text:
            exchange_record.write(
                {
                    "exchange_file": doc.text,
                    "exchange_filename": f"{exchange_record.external_identifier}.txt",
                }
            )
            _logger.info(
                "Ediversa Exchange record created "
                "{exchange_record.external_identifier}"
            )
            component.confirm_document_download(
                exchange_record.external_identifier, exchange_record.company_id
            )
