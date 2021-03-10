# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class GS1InboundNotificationMessage(Component):
    """Process data for Inbound Notification.

    The Warehousing Inbound Notification message
    enables a

    Logistic Services Provider (LSP)

    to inform his

    Logistic Services Client (LSC)

    on the status of goods received on behalf of the client.
    """

    _name = "gs1.process.inbound.notification"
    _inherit = [
        "edi.gs1.input.shipment.mixin",
    ]
    _usage = "gs1.process.warehousingInboundNotification"

    def _process_data(self, data):
        # TODO
        raise NotImplementedError()
