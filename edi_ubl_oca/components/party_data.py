# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIPartyDataUBL(Component):
    """Party data provider specific to UBL."""

    _name = "edi.party.data.ubl"
    _inherit = "edi.party.data"
    _backend_type = "ubl"
