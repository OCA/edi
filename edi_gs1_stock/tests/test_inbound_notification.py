# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from freezegun import freeze_time

# from .common import ShipmentTestCaseBase

# TODO: add inbound notification handling


# class InboundNotificationTestCase(ShipmentTestCaseBase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls._setup_order()
#         cls.exc_type = cls.env.ref(
#             "edi_gs1_stock.edi_exchange_type_inbound_notification"
#         )
#         cls.exc_tmpl = cls.env.ref(
#             "edi_gs1_stock.edi_exchange_template_inbound_notification"
#         )
#         vals = {
#             "model": cls.delivery._name,
#             "res_id": cls.delivery.id,
#             "type_id": cls.exc_type.id,
#             "edi_exchange_state": "input_received",
#             # TODO: set xml value
#         }
#         cls.record = cls.backend.create_record(cls.exc_type.code, vals)

#     @freeze_time("2020-07-09 10:30:00")
#     def test_info_provider_data(self):
#         values = self.exc_tmpl._get_render_values(self.record, shipper=self.carrier)
#         provider = self.exc_tmpl._get_info_provider(self.record, work_ctx=values)
#         expected_shipment = {
#             "shipmentIdentification": {
#                 "additionalShipmentIdentification": {
#                     "attrs": {
#                         # fmt: off
#                         "additionalShipmentIdentificationTypeCode":
#                             "GOODS_RECEIVER_ASSIGNED"
#                         # fmt: on
#                     },
#                     "value": self.delivery.name,
#                 }
#             },
#             "shipper": {
#                 "gln_code": "0000000000123",
#                 "additionalPartyIdentification": {
#                     "attrs": {
#                         # fmt: off
#                         "additionalPartyIdentificationTypeCode":
#                             "BUYER_ASSIGNED_IDENTIFIER_FOR_A_PARTY"
#                         # fmt: on
#                     },
#                     "value": "CARRIER#1",
#                 },
#             },
#             "packageTotal": {
#                 "packageTypeCode": "AF",
#                 "totalPackageQuantity": "2",
#                 "totalGrossWeight": {
#                     "value": self.delivery.weight,
#                     "attrs": {"measurementUnitCode": "KGM"},
#                 },
#             },
#             "warehousingReceiptTypeCode": "REGULAR_RECEIPT",
#             "plannedReceipt": {"logisticEventDateTime": {"date": "2020-07-12"}},
#             "_shipment_items": [
#                 {
#                     "lineItemNumber": 1,
#                     "transactionalTradeItem": {"gtin": "1" * 14},
#                     "_plannedQty": {
#                         "value": 300.0,
#                         "attrs": {"measurementUnitCode": "KGM"},
#                     },
#                 },
#                 {
#                     "lineItemNumber": 2,
#                     "transactionalTradeItem": {"gtin": "2" * 14},
#                     "_plannedQty": {
#                         "value": 200.0,
#                         "attrs": {"measurementUnitCode": "KGM"},
#                     },
#                 },
#                 {
#                     "lineItemNumber": 3,
#                     "transactionalTradeItem": {"gtin": "3" * 14},
#                     "_plannedQty": {
#                         "value": 100.0,
#                         "attrs": {"measurementUnitCode": "KGM"},
#                     },
#                 },
#             ],
#         }
#         info = provider.generate_info().warehousingInboundnotification
#         for k, v in expected_shipment.items():
#             self.assertEqual(
#                 info.warehousingInboundnotificationShipment[k],
#  v, f"{k} does not match"
#             )

#     @freeze_time("2020-07-09 10:30:00")
#     def test_xml(self):
#         record = self.delivery.with_context(
#             edi_exchange_send=False
#         ).action_send_wh_inbound_notification()
#         file_content = record._get_file_content()
#         # FIXME: do proper validation
#         self.assertTrue(
#             file_content.startswith("<warehousing_inbound_notification"), file_content
#         )
