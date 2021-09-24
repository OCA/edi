# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging

from odoo import _, api, exceptions, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized
from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)


try:
    import yaml
except ImportError:
    _logger.debug("`yaml` lib is missing")


class EDIExchangeType(models.Model):
    """
    Define a kind of exchange.
    """

    _name = "edi.exchange.type"
    _description = "EDI Exchange Type"

    backend_id = fields.Many2one(
        string="Backend",
        comodel_name="edi.backend",
        ondelete="set null",
    )
    backend_type_id = fields.Many2one(
        string="Backend type",
        comodel_name="edi.backend.type",
        required=True,
        ondelete="restrict",
    )
    job_channel_id = fields.Many2one(
        comodel_name="queue.job.channel",
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
    ack_type_id = fields.Many2one(
        string="Ack exchange type",
        comodel_name="edi.exchange.type",
        ondelete="set null",
        help="Identify the type of the ack. "
        "If this field is valued it means an hack is expected.",
    )
    advanced_settings_edit = fields.Text(
        string="Advanced YAML settings",
        help="""
            Advanced technical settings as YAML format.
            The YAML structure should reproduce a dictionary.
            The backend might use these settings for automated operations.

            Currently supported conf:

              components:
                generate:
                  usage: $comp_usage
                  work_ctx:
                     opt1: True
                validate:
                  usage: $comp_usage
                check:
                  usage: $comp_usage
                send:
                  usage: $comp_usage
                receive:
                  usage: $comp_usage
                process:
                  usage: $comp_usage

            In any case, you can use these settings
            to provide your own configuration for whatever need you might have.
        """,
    )
    advanced_settings = Serialized(default={}, compute="_compute_advanced_settings")
    model_ids = fields.Many2many(
        "ir.model",
        help="""Modules to be checked for manual EDI generation""",
    )
    enable_domain = fields.Char(
        string="Enable on domain", help="""Filter domain to be checked on Models"""
    )
    enable_snippet = fields.Char(
        string="Enable on snippet",
        help="""Snippet of code to be checked on Models,
        You can use `record` and `exchange_type` here.
        It will be executed if variable result has been defined as True
        """,
    )

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code, backend_id)",
            "The code must be unique per backend",
        )
    ]

    @api.depends("advanced_settings_edit")
    def _compute_advanced_settings(self):
        for rec in self:
            rec.advanced_settings = rec._load_advanced_settings()

    def _load_advanced_settings(self):
        return yaml.safe_load(self.advanced_settings_edit or "") or {}

    def get_settings(self):
        return self.advanced_settings

    @api.constrains("backend_id", "backend_type_id")
    def _check_backend(self):
        for rec in self:
            if not rec.backend_id:
                continue
            if rec.backend_id.backend_type_id != rec.backend_type_id:
                raise exceptions.UserError(_("Backend should respect backend type!"))

    def _make_exchange_filename(self, exchange_record):
        """Generate filename."""
        pattern = self.exchange_filename_pattern
        ext = self.exchange_file_ext
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

    def _get_record_name(self, exchange_record):
        if not exchange_record.res_id or not exchange_record.model:
            return slugify(exchange_record.display_name)
        if hasattr(exchange_record.record, "_get_edi_exchange_record_name"):
            return exchange_record.record._get_edi_exchange_record_name(exchange_record)
        return slugify(exchange_record.record.display_name)
