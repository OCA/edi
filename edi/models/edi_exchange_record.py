# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class EDIExchangeRecord(models.Model):
    """
    Define an exchange record.
    """

    _name = "edi.exchange.record"
    _inherit = "mail.thread"
    _description = "EDI exchange Record"

    name = fields.Char(compute="_compute_name")
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        required=True,
        ondelete="cascade",
        auto_join=True,
    )
    direction = fields.Selection(related="type_id.direction",)
    backend_id = fields.Many2one(
        comodel_name="edi.backend", related="type_id.backend_id",
    )
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
    )
    exchange_identification_code = fields.Char(
        track_visibility="onchange",
        help="Identification of the EDI, useful to search and join other documents",
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

    @api.depends("type_id.code", "model", "res_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "{} - {}".format(
                rec.type_id.name, rec.record.name if rec.model else "Unrelated"
            )

    @api.depends("model", "type_id", "type_id.ack_needed")
    def _compute_exchange_filename(self):
        for rec in self:
            if not rec.exchange_filename:
                rec.exchange_filename = rec.type_id._make_exchange_filename(rec)
            if rec.type_id.ack_needed and not rec.ack_filename:
                rec.ack_filename = rec.type_id._make_exchange_filename(rec, ack=True)

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

    def name_get(self):
        result = []
        for rec in self:
            dt = fields.Datetime.to_string(rec.exchanged_on) if rec.exchanged_on else ""
            name = "[{}] {} {}".format(rec.type_id.name, rec.record.name, dt)
            result.append((rec.id, name))
        return result
