# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import traceback
from io import StringIO

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EdiDocument(models.Model):

    _name = "edi.document"
    _inherit = "mail.thread"
    _description = "Electronic Document"

    res_id = fields.Integer(required=True, index=True, readonly=True)
    res_model = fields.Char(index=True, required=True, readonly=True)
    state = fields.Selection(
        [("to_send", "To Send"), ("sent", "Sent"), ("received", "Received")],
        default="to_send",
        required=True,
        track_visibility="onchange",
    )
    edi_format_id = fields.Many2one("edi.format", required=True, readonly=True)
    attachment_id = fields.Many2one(
        "ir.attachment", string="Main attachment", ondelete="restrict",
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Annexes")
    identification_code = fields.Char(
        track_visibility="onchange",
        help="Identification of the EDI, useful to search and join other documents",
    )
    edi_type = fields.Selection(
        [
            ("outbound", "Outbound"),  # Documents sent
            ("inbound", "Inbound"),  # Documents received"
        ],
        required=True,
        default="outbound",
        readonly=True,
        help="Show direction of the document",
    )
    parent_id = fields.Many2one(
        "edi.document",
        help="Electronic Document was generated following this one",
        readonly=True,
    )
    error = fields.Text()

    @api.depends("res_id", "res_model")
    def name_get(self):
        result = []
        for rec in self:
            result.append(
                (
                    rec.id,
                    "%s - %s"
                    % (
                        self.env[rec.res_model].browse(rec.res_id).display_name,
                        rec.edi_format_id.display_name,
                    ),
                )
            )
        return result

    def action_send(self):
        return self._send()

    def _send(self):
        self.ensure_one()
        if self.state != "to_send":
            raise ValidationError(_("File already sent, cannot be processed"))
        # pylint: disable=E8103
        self.env.cr.execute("SAVEPOINT send_edi_document_%s" % self.id)
        try:
            result = self.edi_format_id._send(self)
            vals = self._send_values(result)
            # pylint: disable=E8103
            self.env.cr.execute("RELEASE SAVEPOINT send_edi_document_%s" % self.id)
        except Exception:

            # pylint: disable=E8103
            self.env.cr.execute("ROLLBACK TO SAVEPOINT send_edi_document_%s" % self.id)
            buff = StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())
            vals = {"error": buff.getvalue()}
        if not vals:
            return False
        return self.write(vals)

    def _send_values(self, result):
        if not result:
            return {}
        vals = {"state": "sent", "error": False}
        if isinstance(result, dict):
            vals.update(result)
        return vals
