# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions

from odoo.addons.component.core import Component


class ApplicationReceiptAcknowledgement(Component):
    """Parse GS1 applicationReceiptAcknowledgement.
    """

    _name = "gs1.input.applicationReceiptAcknowledgement"
    _inherit = "gs1.input.mixin"
    _usage = "gs1.in.ApplicationReceiptAcknowledgement"
    _xsd_schema_path = "static/schemas/gs1/ecom/ApplicationReceiptAcknowledgement.xsd"

    def get_status(self, result):
        try:
            ack = result["applicationReceiptAcknowledgement"][0]
        except IndexError:
            raise exceptions.ValidationError(
                _("applicationReceiptAcknowledgement element not found!")
            )
        status_wrapper = ack["applicationResponseDocumentLevel"][0]
        return status_wrapper["applicationResponseStatusCode"]

    def is_ok(self, result):
        return self.get_status(result) == "RECEIVED"
