# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ediversa_send_invoice = fields.Boolean()
