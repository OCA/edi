# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIPartyData(Component):
    """Default component to lookup for party information."""

    _name = "edi.party.data"
    _inherit = "edi.party.data.mixin"
