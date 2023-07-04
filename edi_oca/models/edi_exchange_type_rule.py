# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models

KIND_HELP = """
* Form button: show a button on the related model form
  when conditions from domain and snippet are satisfied

* Custom: let devs handle a custom behavior with specific developments
"""


class EDIExchangeTypeRule(models.Model):
    """
    Define rules for exchange types.
    """

    _name = "edi.exchange.type.rule"
    _description = "EDI Exchange type rule"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    type_id = fields.Many2one(
        comodel_name="edi.exchange.type",
        required=True,
        ondelete="cascade",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        help="Apply to this model",
        ondelete="cascade",
    )
    model = fields.Char(related="model_id.model")  # Tech field
    enable_domain = fields.Char(
        string="Enable on domain", help="Filter domain to be checked on Models"
    )
    enable_snippet = fields.Char(
        string="Enable on snippet",
        help="""Snippet of code to be checked on Models,
        You can use `record` and `exchange_type` here.
        It will be executed if variable result has been defined as True
        """,
    )
    kind = fields.Selection(
        selection=[
            ("form_btn", "Form button"),
            ("custom", "Custom"),
        ],
        required=True,
        default="form_btn",
        help=KIND_HELP,
    )
    form_btn_label = fields.Char(
        string="Form button label", translate=True, help="Type name used by default"
    )
    form_btn_tooltip = fields.Text(
        string="Form button tooltip",
        translate=True,
        help="Help message visible as tooltip on button h-over",
    )
