# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from lxml import etree
# from odoo import tools
from odoo import _, exceptions
from odoo.tools import DotDict

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
        "edi.output.mixin",
    ]
    _usage = "gs1.warehousingInboundInstructionMessage"
    # _xsd_schema_module = "gs1_stock"
    # _xsd_schema_path = "static/schemas/gs1/ecom/WarehousingInboundInstruction.xsd"

    _work_context_validate_attrs = [
        "record",
        "sender",
        "receiver",
        # instruction specific
        "shipper",  # shipper tag
        "ls_buyer",  # logisticServicesBuyer tag
        "ls_seller",  # logisticServicesSeller tag
    ]

    def generate_info(self):
        return DotDict(self._inbound_instruction())

    def _inbound_instruction(self):
        data = {
            "creationDateTime": self._utc_now(),
            # status code can stay always as it is if we don't send around copies
            "documentStatusCode": "ORIGINAL",
            "documentActionCode": self._document_action_code(),
            # fmt: off
            "warehousingInboundInstructionShipment":
                self._inbound_instruction_shipment(),
            # fmt: on
        }
        return {"warehousingInboundInstruction": data}

    @property
    def replace_existing(self):
        """Pass `replace_existing` to work context to change this value."""
        return getattr(self.work, "replace_existing", False)

    def _document_action_code(self):
        # Brand new file
        code = "ADD"
        if self.replace_existing:
            code = "CHANGE_BY_REFRESH"
        return code

    def _entity_identification(self):
        return self.record.name

    def _inbound_instruction_shipment(self):
        data = {"shipmentIdentification": self._shipment_identification()}
        for key, handler in self._inbound_instruction_shipment_elements().items():
            value = handler()
            # Return empty dict or None in you handler to skip an element
            if value:
                data[key] = value
        return data

    def _inbound_instruction_shipment_elements(self):
        return {
            "shipper": self._shipper,
            "receiver": self._receiver,
            "logisticUnit": self._logistic_unit,
            "packageTotal": self._package_total,
            "warehousingReceiptTypeCode": self._receipt_type_code,
            "plannedReceipt": self._planned_receipt,
        }

    def _shipment_identification(self):
        return {
            "additionalShipmentIdentification": {
                "attrs": {
                    # fmt: off
                    "additionalShipmentIdentificationTypeCode":
                        "GOODS_RECEIVER_ASSIGNED"
                    # fmt: on
                },
                "value": self.record.name,
            }
        }

    def _get_shipper_record(self):
        # We should get the carrier here
        return self.work.shipper

    def _shipper(self):
        """The carrier of the shipment."""

        record = self._get_shipper_record()
        if not record.gln_code and not record.ref:
            raise exceptions.ValidationError(
                _("Either `gln_code` or `ref` is required for shipper: {}").format(
                    record.name
                )
            )
        # `gln` is required in the schema.
        # Depending on your LSP having a fake one and relying on
        # `additionalPartyIdentification` can be enough.
        data = {"gln": "".zfill(13)}
        if record.gln_code:
            data["gln"] = record.gln_code
        if record.ref:
            data["additionalPartyIdentification"] = {
                "attrs": {
                    # fmt: off
                    "additionalPartyIdentificationTypeCode":
                        "BUYER_ASSIGNED_IDENTIFIER_FOR_A_PARTY"
                    # fmt: on
                },
                "value": record.ref,
            }
        return data

    def _get_receiver_record(self):
        return self.work.receiver

    def _receiver(self):
        """Who receives the goods, generally the LSP."""
        record = self._get_receiver_record()
        return {
            "gln": record.gln_code,
        }

    def _logistic_unit(self):
        return {
            # "sscc": "",
            # TODO: pick this from uom or packaging info
            # https://www.unece.org/
            # fileadmin/DAM/cefact/recommendations/rec21/rec21rev4_ecetrd309.pdf
            # "packageTypeCode": "",
        }

    def _package_total(self):
        return DotDict(
            {
                # TODO: would be nice to have mapping based on product packaging
                # but as in some case you simply use the same package types
                # for all the shipments, then is up to integrator to provide
                # proper values by overriding this method.
                # https://www.gs1.se/en/our-standards/Technical-documentation/
                # code-lists/t0137-packaging-type-code/
                # TODO: get generic numbers from picking.
                "packageTypeCode": "AF",
                "totalPackageQuantity": "2",
                "totalGrossWeight": {
                    "value": self.record.weight,
                    "attrs": {"measurementUnitCode": "KGM"},
                },
            }
        )

    def _receipt_type_code(self):
        """TODO use picking priority?

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

    def _inbound_instruction_shipment_items(self):
        item_key = "warehousingInboundInstructionShipmentItem"
        res = []
        for i, item in enumerate(self._get_shipment_items(), start=1):
            res.append({item_key: self._shipment_item(item, i)})
        return res

    def _get_shipment_items(self):
        return self.work.record.move_line_ids

    def _shipment_item(self, item, i=1):
        qty = item.product_uom_qty
        # TODO: get it from line uom
        uom_code = "KGM"
        # Watch out: order is important for XSD validation!
        data = DotDict(
            {
                "lineItemNumber": i,
                "transactionalTradeItem": self._shipment_item_trade_item(item),
            }
        )
        avp_list = self._shipment_item_avp_list(item)
        if avp_list:
            data["avpList"] = avp_list
        data["plannedReceiptQuantity"] = {
            "value": qty,
            "attrs": {"measurementUnitCode": uom_code},
        }
        return data

    def _shipment_item_trade_item(self, item):
        # GTIN is required here.
        # We assume you set it on product's default code.
        # NOTE: GTIN must be 14 chars hence we fill the gap
        # to make XSD validation happy in case it's empty.
        # You are supposed to validate your barcode to match GTIN requirements.
        return {"gtin": item.product_id.barcode or "".zfill(14)}

    def _shipment_item_avp_list(self, item):
        """Hook to add avpList attributes.

        `avpList` can contain an arbitrary set of custom attributes.
        Use `_make_avp_attribute()` to custom items and produce a list here.

        Eg:
            [self._make_avp_attribute("vendorProductName", "Apple")]

        will generate an element like

            <eComStringAttributeValuePairList attributeName="vendorProductName">
                Apple
            </eComStringAttributeValuePairList>
        """
        return []

    def _make_avp_attribute(self, attr_name, value):
        """Generate `eComStringAttributeValuePairList` element."""
        return {
            "eComStringAttributeValuePairList": {
                "attrs": {"attributeName": attr_name},
                "value": value,
            }
        }
