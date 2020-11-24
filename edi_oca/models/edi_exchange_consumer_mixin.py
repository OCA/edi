# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EDIExchangeConsumerMixin(models.AbstractModel):
    """Record that might have related EDI Exchange records
    """

    _name = "edi.exchange.consumer.mixin"
    _description = "Abstract record where exchange records can be assigned"

    exchange_record_ids = fields.One2many(
        "edi.exchange.record",
        inverse_name="res_id",
        domain=lambda r: [("model", "=", r._name)],
    )
    exchange_record_count = fields.Integer(compute="_compute_exchange_record_count")

    def _has_exchange_record(self, exchange_type, backend, extra_domain=False):
        """This function is useful when generating the configuration"""
        domain = [
            ("model", "=", self._name),
            ("res_id", "=", self.id),
            ("backend_id", "=", backend.id),
            ("type_id.code", "=", exchange_type),
        ]
        if extra_domain:
            domain += extra_domain
        return bool(self.env["edi.exchange.record"].search_count(domain))

    @api.depends("exchange_record_ids")
    def _compute_exchange_record_count(self):
        for record in self:
            record.exchange_record_count = len(record.exchange_record_ids)

    def action_view_edi_records(self):
        self.ensure_one()
        action = self.env.ref("edi.act_open_edi_exchange_record_view").read()[0]
        action["domain"] = [("model", "=", self._name), ("res_id", "=", self.id)]
        return action

    def _edi_generate_records(self):
        raise NotImplementedError()
