# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class EDIExchangeRelatedRecord(models.Model):
    """
    Define records related to an exchange record.
    """

    _name = "edi.exchange.related.record"
    _description = "EDI Exchange Related Record"

    exchange_record_id = fields.Many2one(
        comodel_name="edi.exchange.record", required=True,
    )
    model = fields.Char("Model", required=True, readonly=True)
    res_id = fields.Many2oneReference(
        string="Record", required=True, readonly=True, model_field="model",
    )
    name = fields.Char(compute="_compute_name")
    model_name = fields.Char(compute="_compute_model_name")

    _sql_constraints = [
        (
            "exchange_record_record_uniq",
            "unique(model, res_id, exchange_record_id)",
            "A record already existis.",
        ),
    ]

    def _compute_name(self):
        for rec in self:
            rec.name = rec.record.display_name

    def _compute_model_name(self):
        for rec in self:
            rec.model_name = self.env[rec.model]._description

    @property
    def record(self):
        return self.env[self.model].browse(self.res_id)

    def action_open_related_record(self):
        self.ensure_one()
        if not self.model or not self.res_id:
            return {}
        return self.record.get_formview_action()

    @api.model
    def get_related_records(self, rec):
        return self.search([("model", "=", rec._name), ("res_id", "=", rec.id)])
