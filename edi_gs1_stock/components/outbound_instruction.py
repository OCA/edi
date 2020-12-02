# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class GS1OutboundInstructionMessage(Component):
    """Generate data for Outbound Instruction.

    The Warehousing Outbound Instruction message enables a

        Logistic Services Client (LSC)

    to inform his

        Logistic Services Provider (LSP)

    that goods will be shipped.

    Warehousing Outbound Notification Message Definition
    The Warehousing Outbound Notification message
    enables a Logistic Services Provider (LSP) to inform
    his Logistic Services Client (LSC)
    on the status of goods received on behalf of the client.
    """

    _name = "gs1.output.outboundinstruction"
    _inherit = [
        "edi.gs1.output.shipment.mixin",
    ]
    _usage = "edi.output.generate.gs1.warehousingOutboundInstructionMessage.info"

    def _generate_info(self):
        data = {
            "creationDateTime": self._utc_now(),
            # status code can stay always as it is if we don't send around copies
            "documentStatusCode": "ORIGINAL",
            "documentActionCode": self._document_action_code(),
            # fmt: off
            "warehousingOutboundInstructionShipment":
                self._shipment_info(),
            # fmt: on
        }
        return {"warehousingOutboundInstruction": data}

    def _shipment_info_elements(self):
        res = super()._shipment_info_elements()
        res.update(
            {
                "warehousingDespatchTypeCode": self._despatch_type_code,
                "plannedDespatch": self._planned_despatch,
            }
        )
        return res

    def _despatch_type_code(self):
        """TODO get it from picking or mapping configuration or leace

        CROSS-DOCKED_SHIPMENT
            Cross-docked shipment
            One on one cross-dock of an incoming cross-dock shipment.
        WAREHOUSE_CROSS-DOCK_COMBINATION
            Warehouse cross-dock combination
            combination of goods picked from stock
            and goods taken from cross-docked receipts.
        WAREHOUSE_SHIPMENT
            Warehouse shipment.
            All goods are picked from stock.
        """
        code = "WAREHOUSE_SHIPMENT"
        return code

    def _planned_despatch(self):
        # TODO: better info from?
        return {
            "logisticEventDateTime": {
                "date": self.date_to_string(self.record.scheduled_date) or "",
            },
        }
