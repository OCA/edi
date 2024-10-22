# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from .common import ShipmentTestCaseBase


class InboundInstructionTestCase(ShipmentTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_order()
        cls.exc_type = cls.env.ref(
            "edi_gs1_stock.edi_exchange_type_inbound_instruction"
        )
        cls.exc_tmpl = cls.env.ref(
            "edi_gs1_stock.edi_exchange_template_inbound_instruction"
        )
        vals = {
            "model": cls.delivery._name,
            "res_id": cls.delivery.id,
            "type_id": cls.exc_type.id,
        }
        cls.record = cls.backend.create_record(cls.exc_type.code, vals)

    def test_get_template(self):
        template = self.backend._get_template(self.record, "output", "generate")
        self.assertEqual(template, self.exc_tmpl)
        self.assertEqual(
            template.template_id.key, "edi_gs1_stock.edi_exchange_inbound_instruction"
        )

    def test_render_values(self):
        values = self.exc_tmpl._get_render_values(self.record)
        expected = [
            ("sender", self.backend.lsc_partner_id),
            ("receiver", self.backend.lsp_partner_id),
            ("ls_buyer", self.backend.lsc_partner_id),
            ("ls_seller", self.backend.lsp_partner_id),
            ("buyer", self.backend.lsc_partner_id),
            ("seller", self.purchase.partner_id),
        ]
        for k, v in expected:
            self.assertEqual(values[k], v)

        # Detailed test below
        self.assertTrue(values["info"])
        self.assertTrue(values["shipper"])

    def test_info_provider_bad_work_ctx(self):
        with self.assertRaises(AttributeError) as err:
            self.exc_tmpl._get_info_provider(self.record)
            self.assertEqual(
                str(err.exception), "`sender` is required for this component!"
            )

    @freeze_time("2020-07-09 10:30:00")
    def test_info_provider_data(self):
        values = self.exc_tmpl._get_render_values(self.record, shipper=self.carrier)
        provider = self.exc_tmpl._get_info_provider(self.record, work_ctx=values)
        expected_shipment = {
            "shipmentIdentification": {
                "additionalShipmentIdentification": {
                    "attrs": {
                        # fmt: off
                        "additionalShipmentIdentificationTypeCode":
                            "GOODS_RECEIVER_ASSIGNED"
                        # fmt: on
                    },
                    "value": self.delivery.name,
                }
            },
            "shipper": {
                "gln_code": "0000000000123",
                "additionalPartyIdentification": {
                    "attrs": {
                        # fmt: off
                        "additionalPartyIdentificationTypeCode":
                            "BUYER_ASSIGNED_IDENTIFIER_FOR_A_PARTY"
                        # fmt: on
                    },
                    "value": "CARRIER#1",
                },
            },
            "packageTotal": [
                {
                    "packageTypeCode": "AF",
                    "totalPackageQuantity": "2",
                    "totalGrossWeight": {
                        "value": self.delivery.weight,
                        "attrs": {"measurementUnitCode": "KGM"},
                    },
                }
            ],
            "warehousingReceiptTypeCode": "REGULAR_RECEIPT",
            "plannedReceipt": {"logisticEventDateTime": {"date": "2020-07-12"}},
            "_shipment_items": [
                {
                    "lineItemNumber": 1,
                    "note": {},
                    "transactionalTradeItem": {"gtin": "1" * 14},
                    "inventoryDutyFeeTaxStatus": [],
                    "_plannedQty": {
                        "value": 300.0,
                        "attrs": {"measurementUnitCode": "KGM"},
                    },
                },
                {
                    "lineItemNumber": 2,
                    "note": {},
                    "transactionalTradeItem": {"gtin": "2" * 14},
                    "inventoryDutyFeeTaxStatus": [],
                    "_plannedQty": {
                        "value": 200.0,
                        "attrs": {"measurementUnitCode": "KGM"},
                    },
                },
                {
                    "lineItemNumber": 3,
                    "note": {},
                    "transactionalTradeItem": {"gtin": "3" * 14},
                    "inventoryDutyFeeTaxStatus": [],
                    "_plannedQty": {
                        "value": 100.0,
                        "attrs": {"measurementUnitCode": "KGM"},
                    },
                },
            ],
        }
        info = provider.generate_info().warehousingInboundInstruction
        for k, v in expected_shipment.items():
            self.assertEqual(
                info.warehousingInboundInstructionShipment[k], v, f"{k} does not match"
            )

    _schema_path = "edi_gs1:static/schemas/gs1/ecom/WarehousingInboundInstruction.xsd"

    @freeze_time("2020-07-09 10:30:00")
    def test_xml(self):
        record = self.delivery.with_context(
            edi_exchange_send=False
        ).action_send_wh_inbound_instruction()
        file_content = record._get_file_content()
        handler = self._get_xml_handler()
        self.assertEqual(handler.validate(file_content), None)
