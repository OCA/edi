# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import _, api, exceptions, fields, models


class EDIExchangeRecord(models.Model):
    """
    Define an exchange record.
    """

    _name = "edi.exchange.record"
    _inherit = "mail.thread"
    _description = "EDI exchange Record"
    _order = "exchanged_on desc"

    name = fields.Char(compute="_compute_name")
    identifier = fields.Char(required=True, index=True, readonly=True)
    external_identifier = fields.Char(index=True, readonly=True)
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        required=True,
        ondelete="cascade",
        auto_join=True,
    )
    direction = fields.Selection(related="type_id.direction")
    backend_id = fields.Many2one(comodel_name="edi.backend", required=True)
    model = fields.Char(index=True, required=False, readonly=True)
    res_id = fields.Many2oneReference(
        string="Record ID",
        index=True,
        required=False,
        readonly=True,
        model_field="model",
    )
    exchange_file = fields.Binary(attachment=True)
    exchange_filename = fields.Char(
        compute="_compute_exchange_filename", readonly=False, store=True
    )
    exchanged_on = fields.Datetime(
        string="Exchanged on",
        help="Sent or received on this date.",
        compute="_compute_exchanged_on",
        store=True,
        readonly=False,
    )
    ack_file = fields.Binary(attachment=True)
    ack_filename = fields.Char(
        compute="_compute_exchange_filename", readonly=False, store=True
    )
    ack_received_on = fields.Datetime(
        string="ACK received on",
        readonly=True,
        compute="_compute_ack_received_on",
        store=True,
    )
    edi_exchange_state = fields.Selection(
        string="Exchange state",
        readonly=True,
        default="new",
        selection=[
            ("new", "New"),
            # output exchange states
            ("output_pending", "Waiting to be sent"),
            ("output_error_on_send", "error on send"),
            ("output_sent", "Sent"),
            ("output_sent_and_processed", "Sent and processed"),
            ("output_sent_and_error", "Sent and error"),
            # input exchange states
            ("input_pending", "Waiting to be received"),
            ("input_received", "Received"),
            ("input_processed", "Processed"),
            ("input_processed_error", "Error on process"),
        ],
    )
    exchange_error = fields.Text(string="Exchange error", readonly=True)
    ack_needed = fields.Boolean(related="type_id.ack_needed")

    _sql_constraints = [
        ("identifier_uniq", "unique(identifier)", "The identifier must be unique."),
        (
            "external_identifier_uniq",
            "unique(external_identifier)",
            "The external_identifier must be unique.",
        ),
    ]

    @api.depends("type_id.code", "model", "res_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "{} - {}".format(
                rec.type_id.name, rec.record.name if rec.model else "Unrelated"
            )

    @api.depends("model", "type_id", "type_id.ack_needed")
    def _compute_exchange_filename(self):
        for rec in self:
            if not rec.type_id:
                continue
            if not rec.exchange_filename:
                rec.exchange_filename = rec.type_id._make_exchange_filename(rec)
            if rec.type_id.ack_needed and not rec.ack_filename:
                rec.ack_filename = rec.type_id._make_exchange_filename(rec, ack=True)

    @api.depends("edi_exchange_state")
    def _compute_exchanged_on(self):
        for rec in self:
            if rec.edi_exchange_state in ("input_received", "output_sent"):
                rec.exchanged_on = fields.Datetime.now()

    @api.constrains("edi_exchange_state")
    def _constrain_edi_exchange_state(self):
        for rec in self:
            if rec.edi_exchange_state == "new":
                continue
            if not rec.edi_exchange_state.startswith(rec.direction):
                raise exceptions.ValidationError(
                    _("Exchange state must respect direction!")
                )

    @property
    def record(self):
        return self.env[self.model].browse(self.res_id)

    def _set_file_content(
        self, output_string, encoding="utf-8", field_name="exchange_file"
    ):
        """Handy method to no have to convert b64 back and forth."""
        self.ensure_one()
        if not isinstance(output_string, bytes):
            output_string = bytes(output_string, encoding)
        self[field_name] = base64.b64encode(output_string)

    def _get_file_content(self, field_name="exchange_file"):
        """Handy method to no have to convert b64 back and forth."""
        self.ensure_one()
        if not self[field_name]:
            return ""
        return base64.b64decode(self[field_name]).decode()

    def name_get(self):
        result = []
        for rec in self:
            dt = fields.Datetime.to_string(rec.exchanged_on) if rec.exchanged_on else ""
            rec_name = rec.identifier
            if rec.res_id and rec.model:
                rec_name = rec.record.display_name
            name = "[{}] {} {}".format(rec.type_id.name, rec_name, dt)
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, vals):
        vals["identifier"] = self._get_identifier()
        return super().create(vals)

    def _get_identifier(self):
        return self.env["ir.sequence"].next_by_code("edi.exchange")

    @api.constrains("backend_id", "type_id")
    def _constrain_backend(self):
        for rec in self:
            if rec.type_id.backend_id:
                if rec.type_id.backend_id != rec.backend_id:
                    raise exceptions.ValidationError(
                        _("Backend must match with exchange type's backend!")
                    )
            else:
                if rec.type_id.backend_type_id != rec.backend_id.backend_type_id:
                    raise exceptions.ValidationError(
                        _("Backend type must match with exchange type's backend type!")
                    )

    @property
    def _exchange_status_messages(self):
        return {
            # status: message
            "send_ok": _("File %s sent") % self.exchange_filename,
            "send_ko": _(
                "An error happened while sending. Please check exchange record info."
            ),
            "process_ok": _("File %s processed successfully ") % self.exchange_filename,
            "process_ko": _("File %s processed with errors") % self.exchange_filename,
            "ack_received": _("ACK file received."),
            "ack_missing": _("ACK file is required for this exchange but not found."),
            "ack_received_error": _("ACK file received but contains errors."),
        }

    def _exchange_status_message(self, key):
        return self._exchange_status_messages[key]

    def action_exchange_send(self):
        self.ensure_one()
        return self.backend_id.exchange_send(self)

    def action_exchange_process(self):
        self.ensure_one()
        return self.backend_id.exchange_process(self)

    def action_open_related_record(self):
        self.ensure_one()
        if not self.model or not self.res_id:
            return {}
        return self.record.get_formview_action()

    def _trigger_edi_event_make_name(self, name, suffix=None):
        return "on_edi_exchange_{name}{suffix}".format(
            name=name, suffix=("_" + suffix) if suffix else "",
        )

    def _trigger_edi_event(self, name, suffix=None):
        """Trigger a component event linked to this backend and edi exchange."""
        name = self._trigger_edi_event_make_name(name, suffix=suffix)
        self._event(name).notify(self)

    def _notify_done(self):
        self.backend_id._exchange_notify_record(
            self, self._exchange_status_message("process_ok")
        )
        self._trigger_edi_event("done")

    def _notify_error(self, message_key):
        self.backend_id._exchange_notify_record(
            self, self._exchange_status_message(message_key), level="error",
        )
        self._trigger_edi_event("error")

    def _notify_ack_received(self):
        self.backend_id._exchange_notify_record(
            self, self._exchange_status_message("ack_received")
        )
        self._trigger_edi_event("done", suffix="ack_received")

    def _notify_ack_missing(self):
        self.backend_id._exchange_notify_record(
            self, self._exchange_status_message("ack_missing"), level="warning",
        )
        self._trigger_edi_event("done", suffix="ack_missing")

    def _notify_ack_received_error(self):
        self.backend_id._exchange_notify_record(
            self, self._exchange_status_message("ack_received_error"),
        )
        self._trigger_edi_event("done", suffix="ack_received_error")
