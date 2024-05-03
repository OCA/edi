# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIExchangeEDIFACTOutGenerate(Component):
    _name = "edi.output.edifact.out.generate"
    _inherit = "edi.component.output.mixin"
    _usage = "output.generate.edifact"

    def generate(self):
        data = False
        exchange_record = self.exchange_record

        if exchange_record:
            if exchange_record.model == "purchase.order" and exchange_record.res_id:
                order = self.env["purchase.order"].browse(exchange_record.res_id)
                if order:
                    data = order.edifact_purchase_generate_data(exchange_record)
        return data
