# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class GS1InboundInstructionMessage(Component):
    """Generate data for Inbound Instruction.

    The Warehousing Inbound Instruction message enables a

        Logistic Services Client (LSC)

    to inform his

        Logistic Services Provider (LSP)

    that goods will be arriving.

    Warehousing Inbound Notification Message Definition
    The Warehousing Inbound Notification message
    enables a Logistic Services Provider (LSP) to inform
    his Logistic Services Client (LSC)
    on the status of goods received on behalf of the client.
    """

    _name = "gs1.output.inboundinstruction"
    _inherit = [
        "edi.gs1.output.shipment.mixin",
    ]
    _usage = "edi.output.generate.gs1.warehousingInboundInstructionMessage.info"

    def _generate_info(self):
        data = {
            "creationDateTime": self._utc_now(),
            # status code can stay always as it is if we don't send around copies
            "documentStatusCode": "ORIGINAL",
            "documentActionCode": self._document_action_code(),
            # fmt: off
            "warehousingInboundInstructionShipment":
                self._shipment_info(),
            # fmt: on
        }
        return {"warehousingInboundInstruction": data}

    def _shipment_info_elements(self):
        res = super()._shipment_info_elements()
        res.update(
            {
                "warehousingReceiptTypeCode": self._receipt_type_code,
                "plannedReceipt": self._planned_receipt,
            }
        )
        return res

    def _receipt_type_code(self):
        """TODO

        # cross-dock receipt.
        # The instructed receipt is intended to be cross-docked.
        "CROSS-DOCK_RECEIPT",
        # priority receipt.
        # The instructed receipt needs to be processed with high priority.
        "PRIORITY_RECEIPT",
        # regular receipt Normal receipt, no special actions required.
        "REGULAR_RECEIPT",
        # repair receipt.
        # The instructed receipt relates to goods that were under repair.
        "REPAIR_RECEIPT",
        # return
        # The instructed receipt is a return, for example a customer return or a recall.
        "RETURNS",
        """
        code = "REGULAR_RECEIPT"
        return code

    def _planned_receipt(self):
        # TODO: better info from?
        return {
            "logisticEventDateTime": {
                "date": self.date_to_string(self.record.scheduled_date) or "",
            },
        }
