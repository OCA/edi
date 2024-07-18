# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class EDIConfigurationMixin(models.AbstractModel):

    _name = "edi.configuration.mixin"

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
            self._event("on_record_create").notify(
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
            self._event("on_record_write").notify(
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
            self._edi_configuration_log_skip(operation, skip_reason)
            return True
        return False
    
    def _edi_configuration_log_skip(self, operation, reason):
        log_msg = "Skip model=%(model)s op=%(op)s"
        log_args = {
            "model": self._name,
            "op": operation,
            "reason": reason,
        }
        log_msg += ": %(reason)s"
        _logger.debug(log_msg, log_args)
