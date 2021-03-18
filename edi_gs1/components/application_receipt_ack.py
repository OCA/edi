# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions

from odoo.addons.component.core import Component


class ApplicationReceiptAcknowledgement(Component):
    """Parse GS1 applicationReceiptAcknowledgement.
    """

    _name = "gs1.input.applicationReceiptAcknowledgement"
    _inherit = "edi.gs1.input.mixin"
    _usage = "gs1.in.ApplicationReceiptAcknowledgement"
    _xsd_schema_path = "static/schemas/gs1/ecom/ApplicationReceiptAcknowledgement.xsd"

    def _process_data(self, data):
        if not self.is_ok(data):
            # TODO: give a proper message based on the real state
            # options: ERROR, RECEIVED, WARNING
            raise exceptions.ValidationError(_("Exchange not received"))

    def is_ok(self, data):
        return self._get_status(data) == "RECEIVED"

    def _get_status(self, data):
        try:
            ack = data["applicationReceiptAcknowledgement"][0]
        except IndexError:
            # Maybe raise an EDIValidationError?
            raise exceptions.ValidationError(
                _("applicationReceiptAcknowledgement element not found!")
            )
        status_wrapper = ack["applicationResponseDocumentLevel"][0]
        # options: ERROR, RECEIVED, WARNING
        return status_wrapper["applicationResponseStatusCode"]
