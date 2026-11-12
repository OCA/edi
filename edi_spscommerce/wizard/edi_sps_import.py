# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64

from odoo import fields, models


class EdiSpsImportWizard(models.TransientModel):
    """Manual-drop inbound transport for SPS RSX files.

    Creates an ``edi.exchange.record`` in ``input_pending`` state with the
    uploaded payload attached; the receive/process crons (or the chained
    action below) take it from there.
    """

    _name = "edi.sps.import.wizard"
    _description = "Import SPS RSX file"

    exchange_type_id = fields.Many2one(
        comodel_name="edi.exchange.type",
        string="Exchange type",
        required=True,
        domain=[("direction", "=", "input"), ("backend_type_id.code", "=", "sps")],
    )
    exchange_filename = fields.Char(string="Filename")
    exchange_file = fields.Binary(string="RSX file", required=True)

    def action_import(self):
        self.ensure_one()
        exchange_type = self.exchange_type_id
        backend = exchange_type.backend_id
        if not backend:
            backend = self.env["edi.backend"].search(
                [("backend_type_id.code", "=", "sps")], limit=1
            )
        if not backend:
            raise ValueError("No SPS backend configured.")
        record = backend.create_record(
            exchange_type.code,
            {
                "exchange_filename": self.exchange_filename or "imported.xml",
                "edi_exchange_state": "input_pending",
            },
        )
        # Binary fields hand us base64; _set_file_content expects raw content
        record._set_file_content(base64.b64decode(self.exchange_file))
        # Run receive+process right away instead of waiting for the cron.
        # Comment out to exercise the scheduled path.
        record.action_exchange_receive_process_chained()
        return {
            "type": "ir.actions.act_window",
            "res_model": "edi.exchange.record",
            "res_id": record.id,
            "view_mode": "form",
            "target": "current",
        }
