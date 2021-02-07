# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EbillPaymentContract(models.Model):

    _name = "ebill.payment.contract"
    _description = "eBill Payment Contract"

    transmit_method_id = fields.Many2one(
        comodel_name="transmit.method",
        string="Service Name",
        ondelete="restrict",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", required=True, string="Customer"
    )
    name = fields.Char(related="partner_id.name")
    date_start = fields.Date(
        string="Start date",
        required=True,
        default=fields.Date.today,
    )
    date_end = fields.Date(string="End date")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("open", "Open"), ("cancel", "Cancel")],
        required=True,
        default="draft",
    )
    is_valid = fields.Boolean(compute="_compute_is_valid", search="_search_is_valid")

    @api.onchange("state")
    def _onchange_state(self):
        """Change the end date if contract is canceled."""
        if self.state == "cancel" and self.date_end > fields.Date.today():
            self.date_end = fields.Date.today()

    @api.depends("state", "date_start", "date_end")
    def _compute_is_valid(self):
        """Check that the contract is valid

        It is valid if the contract is opened and its start date is in the past
        And his end date is in the future or not set.
        """
        today = fields.Date.today()
        for contract in self:
            contract.is_valid = (
                contract.state == "open"
                and contract.date_start
                and contract.date_start <= today
                and (not contract.date_end or contract.date_end >= today)
            )

    def _search_is_valid(self, operator, value):
        now = fields.Date.today()
        domain = [
            ("state", "=", "open"),
            ("date_start", "<=", now),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", now),
        ]
        valid_contract = self.search(domain)
        if (operator == "=" and value) or (operator == "!=" and not value):
            new_operator = "in"
        else:
            new_operator = "not in"
        return [("id", new_operator, valid_contract.ids)]
