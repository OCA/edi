# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.component.core import AbstractComponent


class EDIExchangeInfoOutputMixin(AbstractComponent):
    """Abstract component mixin to generate GS1 compliant XML files."""

    _name = "edi.output.info.mixin"
    _inherit = "edi.info.provider.mixin"
