# Copyright 2020 ACSONE SA
# Copyright 2021 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
from datetime import datetime

from pytz import timezone, utc

from odoo import _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, groupby

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

    active = fields.Boolean(default=True, inverse="_inverse_active")
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
    code = fields.Char(required=True, copy=False)
    direction = fields.Selection(
        selection=[("input", "Input"), ("output", "Output")], required=True
    )
    exchange_filename_pattern = fields.Char(default="{record_name}-{type.code}-{dt}")
    # TODO make required if exchange_filename_pattern is
    exchange_file_ext = fields.Char()
    # TODO: this flag should be probably deprecated
    # because when an exchange w/o file is pending
    # there's no reason not to generate it.
    # Also this could be controlled more generally w/ edi auto settings.
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
    ack_for_type_ids = fields.Many2many(
        string="Ack for exchange type",
        comodel_name="edi.exchange.type",
        compute="_compute_ack_for_type_ids",
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
                  # set a value for component work context
                  work_ctx:
                     opt1: True
                validate:
                  usage: $comp_usage
                  env_ctx:
                    # set a value for the whole processing env
                    opt2: False
                check:
                  usage: $comp_usage
                send:
                  usage: $comp_usage
                receive:
                  usage: $comp_usage
                process:
                  usage: $comp_usage

              filename_pattern:
                force_tz: Europe/Rome
                date_pattern: %Y-%m-%d-%H-%M-%S

            In any case, you can use these settings
            to provide your own configuration for whatever need you might have.
        """,
    )
    advanced_settings = Serialized(default={}, compute="_compute_advanced_settings")
    rule_ids = fields.One2many(
        comodel_name="edi.exchange.type.rule",
        inverse_name="type_id",
        help="Rules to handle exchanges and UI automatically",
    )
    # Deprecated fields for rules - begin
    # These fields have been deprecated in
    # https://github.com/OCA/edi/pull/797
    # but are kept for backward compat.
    # If you can stop using them now.
    # Anyway, annoying warning messages will be logged.
    # See inverse methods.
    # NOTE: old configurations are migrated automatically on upgrade
    # Yet, if you have data files they might be broken
    # if we delete these fields.
    model_ids = fields.Many2many(
        "ir.model", inverse="_inverse_deprecated_rules_model_ids"
    )
    enable_domain = fields.Char(inverse="_inverse_deprecated_rules_enable_domain")
    enable_snippet = fields.Char(inverse="_inverse_deprecated_rules_enable_snippet")
    model_manual_btn = fields.Boolean(
        inverse="_inverse_deprecated_rules_model_manual_btn"
    )
    deprecated_rule_fields_still_used = fields.Boolean(
        compute="_compute_deprecated_rule_fields_still_used"
    )
    # Deprecated fields for rules - end
    quick_exec = fields.Boolean(
        string="Quick execution",
        help="When active, records of this type will be processed immediately "
        "without waiting for the cron to pass by.",
    )
    partner_ids = fields.Many2many(
        string="Enabled for partners",
        comodel_name="res.partner",
        help=(
            "You can use this field to limit generating/processing exchanges "
            "for specific partners. "
            "Use it directly or within models rules (domain or snippet)."
        ),
    )

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code, backend_id)",
            "The code must be unique per backend",
        )
    ]

    def _inverse_active(self):
        for rec in self:
            # Disable rules if type gets disabled
            if not rec.active:
                rec.rule_ids.active = False

    @api.depends("advanced_settings_edit")
    def _compute_advanced_settings(self):
        for rec in self:
            rec.advanced_settings = rec._load_advanced_settings()

    def _load_advanced_settings(self):
        # TODO: validate settings w/ a schema.
        # Could be done w/ Cerberus or JSON-schema.
        # This would help documenting core and custom keys.
        return yaml.safe_load(self.advanced_settings_edit or "") or {}

    def _compute_ack_for_type_ids(self):
        ack_for = self.search([("ack_type_id", "in", self.ids)])
        by_type_id = dict(groupby(ack_for, lambda x: x.ack_type_id.id))
        for rec in self:
            rec.ack_for_type_ids = [x.id for x in by_type_id.get(rec.id, [])]

    def get_settings(self):
        return self.advanced_settings

    def set_settings(self, val):
        self.advanced_settings_edit = val

    @api.constrains("backend_id", "backend_type_id")
    def _check_backend(self):
        for rec in self:
            if not rec.backend_id:
                continue
            if rec.backend_id.backend_type_id != rec.backend_type_id:
                raise exceptions.UserError(_("Backend should respect backend type!"))

    def _make_exchange_filename_datetime(self):
        """
        Returns current datetime (now) using filename pattern
        which can be set using advanced settings.

        Example:
          filename_pattern:
            force_tz: Europe/Rome
            date_pattern: %Y-%m-%d-%H-%M-%S
        """
        self.ensure_one()
        pattern_settings = self.advanced_settings.get("filename_pattern", {})
        force_tz = pattern_settings.get("force_tz", self.env.user.tz)
        date_pattern = pattern_settings.get("date_pattern", DATETIME_FORMAT)
        tz = timezone(force_tz) if force_tz else None
        now = datetime.now(utc).astimezone(tz)
        return slugify(now.strftime(date_pattern))

    def _make_exchange_filename(self, exchange_record):
        """Generate filename."""
        pattern = self.exchange_filename_pattern
        ext = self.exchange_file_ext
        pattern = pattern + ".{ext}"
        dt = self._make_exchange_filename_datetime()
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

    def is_partner_enabled(self, partner):
        """Check if given partner record is allowed for the current type.

        You can leverage this in your own logic to trigger or not
        certain exchanges for specific partners.

        For instance: a customer might require an ORDRSP while another does not.
        """
        exc_type = self.sudo()
        if exc_type.partner_ids:
            return partner.id in exc_type.partner_ids.ids
        return True

    # API to support deprecated model rules fields - begin
    def _inverse_deprecated_rules_warning(self):
        _fields = ", ".join(
            ["model_ids", "enable_domain", "enable_snippet", "model_manual_btn"]
        )
        _logger.warning(
            "The fields %s are deprecated, "
            "please stop using them in favor of edi.exchange.type.rule",
            _fields,
        )

    def _inverse_deprecated_rules_model_ids(self):
        if self.env.context.get("deprecated_rule_fields_bypass_inverse"):
            return
        self._inverse_deprecated_rules_warning()
        for rec in self:
            for model in rec.model_ids:
                rule = rec._get_rule_by_model(model)
                if not rule:
                    _logger.warning(
                        "New rule for %s created from deprecated `model_ids`",
                        model.model,
                    )
                    rec.rule_ids += rec._inverse_deprecated_rules_create(model)
            rules_to_delete = rec.rule_ids.browse()
            for rule in rec.rule_ids:
                if rule.model_id not in rec.model_ids:
                    _logger.warning(
                        "Rule for %s deleted from deprecated `model_ids`",
                        rule.model_id.model,
                    )
                    rules_to_delete |= rule
            rules_to_delete.unlink()

    def _inverse_deprecated_rules_enable_domain(self):
        if self.env.context.get("deprecated_rule_fields_bypass_inverse"):
            return
        self._inverse_deprecated_rules_warning()
        for rec in self:
            for model in rec.model_ids:
                rule = rec._get_rule_by_model(model)
                if rule:
                    _logger.warning(
                        "Rule for %s domain updated from deprecated `enable_domain`",
                        model.model,
                    )
                    rule.enable_domain = rec.enable_domain

    def _inverse_deprecated_rules_enable_snippet(self):
        if self.env.context.get("deprecated_rule_fields_bypass_inverse"):
            return
        self._inverse_deprecated_rules_warning()
        for rec in self:
            for model in rec.model_ids:
                rule = rec._get_rule_by_model(model)
                if rule:
                    _logger.warning(
                        "Rule for %s snippet updated from deprecated `enable_snippet`",
                        model.model,
                    )
                    rule.enable_snippet = rec.enable_snippet

    def _inverse_deprecated_rules_model_manual_btn(self):
        if self.env.context.get("deprecated_rule_fields_bypass_inverse"):
            return
        self._inverse_deprecated_rules_warning()
        for rec in self:
            for model in rec.model_ids:
                rule = rec._get_rule_by_model(model)
                if rule:
                    _logger.warning(
                        "Rule for %s btn updated from deprecated `model_manual_btn`",
                        model.model,
                    )
                    rule.kind = "form_btn" if self.model_manual_btn else "custom"

    def _get_rule_by_model(self, model):
        return self.rule_ids.filtered(lambda x: x.model_id == model)

    def _inverse_deprecated_rules_create(self, model):
        kind = "form_btn" if self.model_manual_btn else "custom"
        vals = {
            "type_id": self.id,
            "model_id": model.id,
            "kind": kind,
            "name": "Default",
            "enable_snippet": self.enable_snippet,
            "enable_domain": self.enable_domain,
        }
        return self.rule_ids.create(vals)

    @api.depends("model_ids", "enable_domain", "enable_snippet", "model_manual_btn")
    def _compute_deprecated_rule_fields_still_used(self):
        for rec in self:
            rec.deprecated_rule_fields_still_used = (
                rec._deprecated_rule_fields_still_used()
            )

    def _deprecated_rule_fields_still_used(self):
        for fname in ("model_ids", "enable_snippet", "enable_domain"):
            if self[fname]:
                return True

    def button_wipe_deprecated_rule_fields(self):
        _fields = ["model_ids", "enable_domain", "enable_snippet", "model_manual_btn"]
        deprecated_vals = {}.fromkeys(_fields, None)
        self.with_context(deprecated_rule_fields_bypass_inverse=True).write(
            deprecated_vals
        )

    # API to support deprecated model rules fields - end
