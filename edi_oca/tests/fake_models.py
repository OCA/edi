# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class EdiExchangeConsumerTest(models.Model):
    _name = "edi.exchange.consumer.test"
    _inherit = ["edi.exchange.consumer.mixin"]
    _description = "Model used only for test"

    name = fields.Char()
    edi_config_ids = fields.Many2many(
        string="EDI Purchase Config Ids",
        comodel_name="edi.configuration",
        relation="test_edi_configuration_rel",
        column1="record_id",
        column2="conf_id",
        domain="[('model_name', '=', 'edi.exchange.consumer.test')]",
    )

    def _get_edi_exchange_record_name(self, exchange_record):
        return self.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        operation = "create"

        new_records = self.browse()
        new_vals_list = []

        for rec, vals in zip(records, vals_list):
            if not rec._edi_configuration_skip(operation):
                new_records |= rec
                new_vals_list.append(vals)

        if new_records:
            self._event("on_record_create_configuration").notify(
                new_records,
                operation=operation,
                vals=new_vals_list,
            )
        return records

    def write(self, vals):
        operation = "write"
        new_records = self.browse()

        for rec in self:
            if not rec._edi_configuration_skip(operation):
                new_records |= rec

        old_vals = {}
        for record in new_records:
            old_vals[record.id] = {field: record[field] for field in vals.keys()}

        res = super().write(vals)

        new_values = {}
        for record in new_records:
            new_values[record.id] = {field: record[field] for field in vals.keys()}

        if new_values:
            self._event("on_record_write_configuration").notify(
                new_records,
                operation=operation,
                old_vals=old_vals,
                vals=new_values,
            )
        return res

    def _edi_configuration_skip(self, operation):
        skip_reason = None
        if self.env.context.get("edi_skip_configuration"):
            skip_reason = "edi_skip_configuration ctx key found"
        # TODO: Add more skip cases
        if skip_reason:
            return True
        return False
