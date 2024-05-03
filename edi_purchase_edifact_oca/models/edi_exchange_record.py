# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.addons.edi_oca.models.edi_exchange_record import EDIExchangeRecord


class EDIExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    _rollback_state_mapping = {
        **EDIExchangeRecord._rollback_state_mapping,
        "input_processed": "input_received",
    }
