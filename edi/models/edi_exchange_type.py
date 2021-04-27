# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models

from odoo.addons.http_routing.models.ir_http import slugify


class EDIExchangeType(models.Model):
    """
    Define a kind of exchange.
    """

    _name = "edi.exchange.type"
    _description = "EDI Exchange Type"

    backend_id = fields.Many2one(
        string="EDI backend", comodel_name="edi.backend", ondelete="set null",
    )
    backend_type_id = fields.Many2one(
        string="EDI Backend type",
        comodel_name="edi.backend.type",
        required=True,
        ondelete="restrict",
    )
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    direction = fields.Selection(
        selection=[("input", "Input"), ("output", "Output")], required=True
    )
    exchange_filename_pattern = fields.Char(default="{record_name}-{type.code}-{dt}")
    # TODO make required if exchange_filename_pattern is
    exchange_file_ext = fields.Char()
    exchange_file_auto_generate = fields.Boolean(
        help="Auto generate output for records missing their payload. "
        "If active, a cron will take care of generating the output when not set yet. "
    )
    ack_needed = fields.Boolean()
    ack_name = fields.Char()
    ack_code = fields.Char()
    ack_filename_pattern = fields.Char(default="{type.exchange_filename_pattern}.ack")
    ack_file_ext = fields.Char(default="")

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code, backend_id)",
            "The code must be unique per backend",
        )
    ]

    @api.constrains("backend_id", "backend_type_id")
    def _check_backend(self):
        for rec in self:
            if not rec.backend_id:
                continue
            if rec.backend_id.backend_type_id != rec.backend_type_id:
                raise exceptions.UserError(_("Backend should respect backend type!"))

    def _make_exchange_filename(self, exchange_record, ack=False):
        """Generate filename."""
        pattern = self.exchange_filename_pattern
        ext = self.exchange_file_ext
        if ack:
            pattern = self.ack_filename_pattern
            ext = self.ack_file_ext
        pattern = pattern + ".{ext}"
        dt = slugify(fields.Datetime.to_string(fields.Datetime.now()))
        record_name = self._get_record_name(exchange_record)
        record = exchange_record
        if exchange_record.model and exchange_record.res_id:
            record = exchange_record.record
        return pattern.format(
            exchange_record=exchange_record,
            record=record,
            record_name=record_name,
            type=self,
            dt=dt,
            ext=ext,
        )

    def _get_record_name(self, record):
        if not record.res_id or not record.model:
            return slugify(record.display_name)
        if hasattr(record.record, "_get_edi_exchange_record_name"):
            return record.record._get_edi_exchange_record_name(record, self)
        return slugify(record.record.display_name)
