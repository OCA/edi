# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from uuid import uuid4

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.edi_gs1.tests.common import BaseXMLTestCase


class DeliveryMixin(object):
    @classmethod
    def _create_purchase_order(cls, values, view=None):
        """Create a purchase order

        :return: purchase order
        """
        po = Form(cls.env["purchase.order"], view=view)
        po.partner_ref = str(uuid4())[:6]
        po.date_planned = fields.Date.today()
        for k, v in values.items():
            setattr(po, k, v)
        return po.save()

    @classmethod
    def _create_purchase_order_line(cls, purchase_order, view=None, **kw):
        """
        Create a purchase order line for give order
        :return: line
        """
        values = {}
        values.update(kw)
        po = Form(purchase_order, view=view)
        with po.order_line.new() as po_line:
            for k, v in values.items():
                setattr(po_line, k, v)
        return po.save()


class InboundInstructionTestCaseBase(BaseXMLTestCase, DeliveryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # cls.type_out3 = cls._create_exchange_type(
        #     name="Template output 3",
        #     direction="output",
        #     code="test_type_out3",
        #     exchange_file_ext="xml",
        #     exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        # )
        # model = cls.env["edi.exchange.template.output"]
        # cls.tmpl_out3 = model.create(
        #     {
        #         "name": "Out 3",
        #         "type_id": cls.type_out3.id,
        #         "type": "qweb",
        #         "key": "edi_exchange.test_output3",
        #         "arch": """
        #         <t t-name="edi_exchange.test_output3">
        #         {}
        #         </t>
        #     """.format(WH_INBOUND_TMPL),
        #     }
        # )
        # vals = {
        #     "model": cls.partner._name,
        #     "res_id": cls.partner.id,
        #     "type_id": cls.type_out3.id,
        # }
        # cls.record3 = cls.backend.create_record("test_type_out3", vals)

    @classmethod
    def _setup_order(cls):
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_a.barcode = "1" * 14
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_b.barcode = "2" * 14
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.product_c.barcode = "3" * 14
        cls.purchase = cls._create_purchase_order(
            {
                "partner_id": cls.env.ref("base.res_partner_10"),
                "date_planned": "2020-07-12",
            }
        )
        lines = [
            {"product_id": cls.product_a, "product_qty": 300},
            {"product_id": cls.product_b, "product_qty": 200},
            {"product_id": cls.product_c, "product_qty": 100},
        ]
        for line in lines:
            cls._create_purchase_order_line(cls.purchase, **line)

        cls.purchase.button_approve()
        cls.delivery_order = cls.purchase.picking_ids[0]
        cls.carrier = cls.env.ref("base.res_partner_4")
        cls.carrier.gln_code = "44".zfill(13)
        cls.carrier.ref = "CARRIER#1"

    def _get_handler(
        self, usage="gs1.warehousingInboundInstructionMessage", work_ctx=None, **kw
    ):
        default_work_ctx = dict(
            record=self.delivery_order,
            sender=self.lsc_partner,
            receiver=self.lsp_partner,
            shipper=self.carrier,
            instance_identifier="WH-IN-TEST-01",
            ls_buyer=self.lsc_partner,
            ls_seller=self.lsp_partner,
        )
        default_work_ctx.update(work_ctx or {})
        return self.backend._get_component(work_ctx=default_work_ctx, usage=usage, **kw)


class InboundInstructionTestCase(InboundInstructionTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_order()

    @freeze_time("2020-07-09 10:30:00")
    def test_business_header_data(self):
        handler = self._get_handler()
        result = handler._business_header()
        expected_doc_id = {
            "@ns": "sh",
            "Standard": {"@ns": "sh", "@value": "GS1"},
            "TypeVersion": {"@ns": "sh", "@value": "3.4"},
            "InstanceIdentifier": {"@ns": "sh", "@value": "WH-IN-TEST-01"},
            "Type": {"@ns": "sh", "@value": ""},
            "MultipleType": {"@ns": "sh", "@value": "false"},
            "CreationDateAndTime": {"@ns": "sh", "@value": "2020-07-09T10:30:00"},
        }
        self.assertEqual(
            result["StandardBusinessDocumentHeader"]["DocumentIdentification"],
            expected_doc_id,
        )

    @freeze_time("2020-07-09 10:30:00")
    def test_instruction_data(self):
        handler = self._get_handler()
        result = handler._inbound_instruction()
        expected = {
            "warehousingInboundInstruction": {
                "creationDateTime": "2020-07-09T10:30:00",
                "documentStatusCode": "ORIGINAL",
                "documentActionCode": "ADD",
                "warehousingInboundInstructionIdentification": {
                    "entityIdentification": self.delivery_order.name,
                },
                "logisticServicesBuyer": {"gln": "0000000000002"},
                "logisticServicesSeller": {"gln": "0000000000001"},
                "warehousingInboundInstructionShipment": [
                    {
                        "shipmentIdentification": {
                            "additionalShipmentIdentification": {
                                "@attrs": {
                                    # fmt: off
                                    "additionalShipmentIdentificationTypeCode":
                                        "GOODS_RECEIVER_ASSIGNED"
                                    # fmt: on
                                },
                                "@value": self.delivery_order.name,
                            }
                        }
                    },
                    {
                        "shipper": {
                            "gln": "0000000000044",
                            "additionalPartyIdentification": {
                                "@attrs": {
                                    # fmt: off
                                    "additionalPartyIdentificationTypeCode":
                                        "BUYER_ASSIGNED_IDENTIFIER_FOR_A_PARTY"
                                    # fmt: on
                                },
                                "@value": "CARRIER#1",
                            },
                        }
                    },
                    {"receiver": {"gln": "0000000000001"}},
                    {
                        "packageTotal": {
                            "packageTypeCode": "AF",
                            "totalPackageQuantity": "2",
                            "totalGrossWeight": {
                                "@value": self.delivery_order.weight,
                                "@attrs": {"measurementUnitCode": "KGM"},
                            },
                        }
                    },
                    {"warehousingReceiptTypeCode": "REGULAR_RECEIPT"},
                    {
                        "plannedReceipt": {
                            "logisticEventDateTime": {"date": "2020-07-12"}
                        }
                    },
                    {
                        "warehousingInboundInstructionShipmentItem": {
                            "lineItemNumber": 1,
                            "transactionalTradeItem": {"gtin": "1" * 14},
                            "plannedReceiptQuantity": {
                                "@value": 300.0,
                                "@attrs": {"measurementUnitCode": "KGM"},
                            },
                        }
                    },
                    {
                        "warehousingInboundInstructionShipmentItem": {
                            "lineItemNumber": 2,
                            "transactionalTradeItem": {"gtin": "2" * 14},
                            "plannedReceiptQuantity": {
                                "@value": 200.0,
                                "@attrs": {"measurementUnitCode": "KGM"},
                            },
                        }
                    },
                    {
                        "warehousingInboundInstructionShipmentItem": {
                            "lineItemNumber": 3,
                            "transactionalTradeItem": {"gtin": "3" * 14},
                            "plannedReceiptQuantity": {
                                "@value": 100.0,
                                "@attrs": {"measurementUnitCode": "KGM"},
                            },
                        }
                    },
                ],
            }
        }
        self.assertEqual(result, expected)

    @freeze_time("2020-07-09 10:30:00")
    def test_xml(self):
        handler = self._get_handler()
        result = handler.generate_xml()
        self._dev_write_example_file(__file__, "inbound_instruction.xml", result)
        self.assertFalse(handler.validate_schema(result, raise_on_fail=True))
        self.assertXmlDocument(result)
        # self.assertXpathsExist(root, paths)
        # self.assertXmlEquivalentOutputs(self.flatten(result), self.flatten(expected))
