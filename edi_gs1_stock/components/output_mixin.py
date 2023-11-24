# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions
from odoo.tools import DotDict

from odoo.addons.component.core import AbstractComponent


class GS1OutputShipmentMessageMixin(AbstractComponent):
    """Common gs1 output shipment mixin.
    """

    _name = "edi.gs1.output.shipment.mixin"
    _inherit = [
        "edi.gs1.output.mixin",
    ]

    @property
    def _work_context_validate_attrs(self):
        return super()._work_context_validate_attrs + [
            # instruction specific
            "shipper",  # shipper tag
            "ls_buyer",  # logisticServicesBuyer tag
            "ls_seller",  # logisticServicesSeller tag
        ]

    def _shipment_info(self):
        data = {"shipmentIdentification": self._shipment_identification()}
        for key, handler in self._shipment_info_elements().items():
            value = handler()
            # Return empty dict or None in you handler to skip an element
            if value:
                data[key] = value
        return data

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

    def _shipment_info_elements(self):
        return {
            "shipper": self._shipper,
            "packageTotal": self._package_total,
            "_shipment_items": self._shipment_items,
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
        data = {"gln_code": "".zfill(13)}
        if record.gln_code:
            data["gln_code"] = record.gln_code
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

    def _package_total(self):
        return [
            DotDict(
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
            ),
        ]

    def _shipment_items(self):
        res = []
        for i, item in enumerate(self._get_shipment_items(), start=1):
            res.append(self._shipment_item(item, i))
        return res

    def _get_shipment_items(self):
        return self.record.move_line_ids

    def _shipment_item(self, item, i=1):
        qty = item.product_uom_qty
        # TODO: get it from line uom
        uom_code = "KGM"
        # Watch out: order is important for XSD validation!
        inventory_fee_tax_status = [
            DotDict(v) for v in self._inventory_duty_fee_tax_status(item)
        ]
        data = DotDict(
            {
                "lineItemNumber": i,
                "transactionalTradeItem": self._shipment_item_trade_item(item),
                "note": self._shipment_item_note(item),
                "inventoryDutyFeeTaxStatus": inventory_fee_tax_status,
            }
        )
        avp_list = self._shipment_item_avp_list(item)
        if avp_list:
            data["avpList"] = avp_list
        # NOTE: `_plannedQty` does not match the final key
        # which vary depending on the message
        # (eg: plannedReceiptQuantity, plannedDespatchQuantity)
        # You should handle it properly in your template.
        data["_plannedQty"] = {
            "value": qty,
            "attrs": {"measurementUnitCode": uom_code},
        }
        return data

    def _inventory_duty_fee_tax_status(self, item):
        """

        :param item:
        :return: list of dict
        """
        return []

    def _shipment_item_note(self, item):
        return {}

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
