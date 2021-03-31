# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class GS1InputShipmentMessageMixin(AbstractComponent):
    """Common gs1 input shipment mixin.
    """

    _name = "edi.gs1.input.shipment.mixin"
    _inherit = [
        "edi.gs1.input.mixin",
    ]

    def _process_data(self, data):
        import pdb

        pdb.set_trace()
