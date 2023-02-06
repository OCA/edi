# Copyright 2023 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo import fields, models


class EdiPunchoutTransaction(models.TransientModel):
    _name = "edi.punchout.transaction"
    _description = "A transaction for a punchout session"
    _rec_name = "transaction_id"
    _order = "create_date desc"

    transaction_id = fields.Char(required=True, default=lambda self: str(uuid4()))
    session_id = fields.Char(required=True)
    client_key = fields.Char(required=True, default=lambda self: str(uuid4()))
    account_id = fields.Many2one("edi.punchout.account", required=True)
    order_id = fields.Many2one("purchase.order")
    request = fields.Text()
    exception = fields.Text()
