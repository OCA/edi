# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiExchangeRecordCreateWiz(models.TransientModel):
    _name = "edi.exchange.record.create.wiz"
    _description = "Create an Exchange Record"

    res_id = fields.Integer(required=True)
    model = fields.Char(required=True)
    exchange_type_id = fields.Many2one("edi.exchange.type", required=True)
    backend_type_id = fields.Many2one(
        "edi.backend.type", related="exchange_type_id.backend_type_id"
    )
    backend_id = fields.Many2one("edi.backend", required=True)

    def create_edi(self):
        record = self.env[self.model].browse(self.res_id)
        exchange_record = record._edi_create_exchange_record(
            self.exchange_type_id, self.backend_id
        )
        record._event("on_edi_generate_manual").notify(record, exchange_record)
        return exchange_record.get_formview_action()
