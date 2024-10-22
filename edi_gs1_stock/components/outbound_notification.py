# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class GS1OutboundNotificationMessage(Component):
    """Process data for Outbound Notification.

    The Warehousing Outbound Notification message
    enables a

        Logistic Services Provider (LSP)

    to inform his

        Logistic Services Client (LSC)

    on the status of goods received on behalf of the client.
    """

    _name = "gs1.process.outbound.notification"
    _inherit = [
        "edi.gs1.input.shipment.mixin",
    ]
    _usage = "gs1.process.warehousingOutboundNotification"

    def _process_data(self, data):
        # TODO
        raise NotImplementedError()
