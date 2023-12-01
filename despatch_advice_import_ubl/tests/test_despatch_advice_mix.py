# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from base64 import b64encode

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestDespatchAdviceMix(TransactionCase):
    @classmethod
    def setUpClass(cls):
        """
        Semi integration test : grab several DO for one PO
        and check that everything is created properly:
        Backorders, cancelled moves, etc
        """
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        Product = cls.env["product.product"]
        cls.supplier = cls.env.ref("base.res_partner_12")
        cls.supplier.vat = "BE0477472701"
        cls.env.user.company_id.partner_id.vat = "BE0421801233"
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
            }
        )

        cls.p1 = Product.create(
            {
                "name": "CYDECTIN 0,1% ORAL DRENCH 1L",
                "default_code": "1354307",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "P1"})
                ],
            }
        )
        cls.line1 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p1.id,
                "name": cls.p1.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 60,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 51.4,
            }
        )

        cls.p2 = Product.create(
            {
                "name": "CYDECTIN TRICLAMOX OVIN 1 L",
                "default_code": "10005578",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p2"})
                ],
            }
        )
        cls.line2 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p2.id,
                "name": cls.p2.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 40,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 78.65,
            }
        )

        cls.p3 = Product.create(
            {
                "name": "VANGUARD DA2PI-CPV 25X1D",
                "default_code": "10001458",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p3"})
                ],
            }
        )
        cls.line3 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p3.id,
                "name": cls.p3.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 24,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 96.32,
            }
        )

        cls.p4 = Product.create(
            {
                "name": "APOQUEL  5,4MG 100CP",
                "default_code": "10022152",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p4"})
                ],
            }
        )
        cls.line4 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p4.id,
                "name": cls.p4.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 96,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 73.86,
            }
        )

        cls.p5 = Product.create(
            {
                "name": "DOGMINTH PATE TUBE 24GR",
                "default_code": "10002655",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p5"})
                ],
            }
        )
        cls.line5 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p5.id,
                "name": cls.p5.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 280,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 7.2,
            }
        )

        cls.p6 = Product.create(
            {
                "name": "RISPOVAL IBR INACT 100ML",
                "default_code": "10001112",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p6"})
                ],
            }
        )
        cls.line6 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p6.id,
                "name": cls.p6.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 20,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 114.36,
            }
        )

        cls.p7 = Product.create(
            {
                "name": "MODERIN 32MG   30CP",
                "default_code": "10005211",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p7"})
                ],
            }
        )
        cls.line7 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p7.id,
                "name": cls.p7.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 10,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 47.62,
            }
        )

        cls.p8 = Product.create(
            {
                "name": "CIDR  1,38gr BOITE DE 10",
                "default_code": "10002949",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p8"})
                ],
            }
        )
        cls.line8 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p8.id,
                "name": cls.p8.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 40,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 116.83,
            }
        )

        cls.p9 = Product.create(
            {
                "name": "VERSICAN+ BB ORAL 10x1d",
                "default_code": "10022422",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p9"})
                ],
            }
        )
        cls.line9 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p9.id,
                "name": cls.p9.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 20,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 93.08,
            }
        )

        cls.p10 = Product.create(
            {
                "name": "VERSICAN+ BBPi IN 10x1d",
                "default_code": "10023409",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p10"})
                ],
            }
        )
        cls.line10 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p10.id,
                "name": cls.p10.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 20,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 97.68,
            }
        )

        cls.p11 = Product.create(
            {
                "name": "CONVENIA SOL INJ 10ml",
                "default_code": "10007669",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p11"})
                ],
            }
        )
        cls.line11 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p11.id,
                "name": cls.p11.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 120,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 150.27,
            }
        )

        cls.p12 = Product.create(
            {
                "name": "WITNESS LH 6x1 TEST",
                "default_code": "10012140",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p12"})
                ],
            }
        )
        cls.line12 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p12.id,
                "name": cls.p12.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 1,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 134.32,
            }
        )

        cls.p13 = Product.create(
            {
                "name": "WITNESS RELAXIN 5x1 TEST GESTATION",
                "default_code": "10010958",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p13"})
                ],
            }
        )
        cls.line13 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p13.id,
                "name": cls.p13.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 2,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 92.37,
            }
        )

        cls.p14 = Product.create(
            {
                "name": "ACEGON 10x6ML",
                "default_code": "10010146",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p14"})
                ],
            }
        )
        cls.line14 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p14.id,
                "name": cls.p14.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 4,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 99.13,
            }
        )

        cls.p15 = Product.create(
            {
                "name": "EQUEST GEL ORAL 700kg",
                "default_code": "10009831",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p15"})
                ],
            }
        )
        cls.line15 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p15.id,
                "name": cls.p15.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 480,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 16.62,
            }
        )

        cls.p16 = Product.create(
            {
                "name": "WITNESS GIARDIA 5 TESTS",
                "default_code": "10009407",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p16"})
                ],
            }
        )
        cls.line16 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p16.id,
                "name": cls.p16.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 1,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 58.12,
            }
        )

        cls.p17 = Product.create(
            {
                "name": "CATMINTH PATE SERINGUE 3GR",
                "default_code": "10003022",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p17"})
                ],
            }
        )
        cls.line17 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p17.id,
                "name": cls.p17.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 400,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 6.07,
            }
        )

        cls.p18 = Product.create(
            {
                "name": "FENDOV 1250 12 BOLI",
                "default_code": "10006920",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p18"})
                ],
            }
        )
        cls.line18 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p18.id,
                "name": cls.p18.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 30,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 232.56,
            }
        )

        cls.p19 = Product.create(
            {
                "name": "FEVAXYN PENTOFEL 10X1D",
                "default_code": "10004344",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p19"})
                ],
            }
        )
        cls.line19 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p19.id,
                "name": cls.p19.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 160,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 164.05,
            }
        )

        cls.p20 = Product.create(
            {
                "name": "VANGUARD CPV-LEPTO 25x1D",
                "default_code": "10001455",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p20"})
                ],
            }
        )
        cls.line20 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p20.id,
                "name": cls.p20.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 5,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 88.73,
            }
        )

        cls.p21 = Product.create(
            {
                "name": "VANGUARD DA2PI-CPV-LEPTO 25x1D (7)",
                "default_code": "10001457",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p21"})
                ],
            }
        )
        cls.line21 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p21.id,
                "name": cls.p21.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 30,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 123.60,
            }
        )

        cls.p22 = Product.create(
            {
                "name": "VANGUARD LEPTO 25x1D",
                "default_code": "10001459",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p22"})
                ],
            }
        )
        cls.line22 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p22.id,
                "name": cls.p22.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 10,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 37.79,
            }
        )

        cls.p23 = Product.create(
            {
                "name": "VERSICAN+ DHPPI 25x1d",
                "default_code": "10011717",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p23"})
                ],
            }
        )
        cls.line23 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p23.id,
                "name": cls.p23.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 30,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 94.93,
            }
        )

        cls.p24 = Product.create(
            {
                "name": "VERSICAN+ DHPPI/L4 25x1d",
                "default_code": "10011718",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p24"})
                ],
            }
        )
        cls.line24 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p24.id,
                "name": cls.p24.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 200,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 156.90,
            }
        )

        cls.p25 = Product.create(
            {
                "name": "VERSICAN+ L4 25x1d",
                "default_code": "10011728",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p25"})
                ],
            }
        )
        cls.line25 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p25.id,
                "name": cls.p25.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 60,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 65.41,
            }
        )

        cls.p26 = Product.create(
            {
                "name": "VERSICAN+ PI 25x1d",
                "default_code": "10011736",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p26"})
                ],
            }
        )
        cls.line26 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p26.id,
                "name": cls.p26.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 40,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 53.73,
            }
        )

        cls.p27 = Product.create(
            {
                "name": "VERSIFEL FELV 25x1d",
                "default_code": "10009541",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p27"})
                ],
            }
        )
        cls.line27 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p27.id,
                "name": cls.p27.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 15,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 277.55,
            }
        )

        cls.p28 = Product.create(
            {
                "name": "VERSIGUARD RABIES 10x1d",
                "default_code": "10016049",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p28"})
                ],
            }
        )
        cls.line28 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p28.id,
                "name": cls.p28.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 30,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 24.14,
            }
        )

        cls.p29 = Product.create(
            {
                "name": "WITNESS FELV-FIV 10x1 TEST",
                "default_code": "10009061",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p29"})
                ],
            }
        )
        cls.line29 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p29.id,
                "name": cls.p29.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 2,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 154.00,
            }
        )

        cls.p30 = Product.create(
            {
                "name": "WITNESS FELV-FIV 5x1 TEST",
                "default_code": "10006252",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "p30"})
                ],
            }
        )
        cls.line30 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.p30.id,
                "name": cls.p30.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 2,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 80.87,
            }
        )
        cls.purchase_order.button_confirm()
        cls.picking = cls.purchase_order.picking_ids

        cls.DespatchAdviceImport = cls.env["despatch.advice.import"]

        with file_open("despatch_advice_import_ubl/tests/files/do_mix1.xml", "rb") as f:
            cls.despatch_advice_xml1 = f.read()

        with file_open("despatch_advice_import_ubl/tests/files/do_mix2.xml", "rb") as f:
            cls.despatch_advice_xml2 = f.read()

    def test_despatch_advice_import(self):

        xml_content1 = self.despatch_advice_xml1.decode("utf-8").format(
            order_id=self.purchase_order.name,
            line_1_id=self.line1.id,
            line_2_id=self.line2.id,
            line_4_id=self.line4.id,
            line_7_id=self.line7.id,
            line_8_id=self.line8.id,
            line_12_id=self.line12.id,
            line_13_id=self.line13.id,
            line_14_id=self.line14.id,
            line_15_id=self.line15.id,
            line_16_id=self.line16.id,
            line_17_id=self.line17.id,
            line_18_id=self.line18.id,
            line_29_id=self.line29.id,
            line_30_id=self.line30.id,
        )

        xml_encoded_doc1 = b64encode(xml_content1.encode("utf-8"))
        despatch_import = self.DespatchAdviceImport.create(
            {"document": xml_encoded_doc1, "filename": "do_mix1.xml"}
        )
        despatch_import.process_document()

        po_moves = self.line21.move_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )

        self.assertTrue(po_moves)

        xml_content2 = self.despatch_advice_xml2.decode("utf-8").format(
            order_id=self.purchase_order.name,
            line_3_id=self.line3.id,
            line_6_id=self.line6.id,
            line_9_id=self.line9.id,
            line_10_id=self.line10.id,
            line_11_id=self.line11.id,
            line_19_id=self.line19.id,
            line_20_id=self.line20.id,
            line_21_id=self.line21.id,
            line_22_id=self.line22.id,
            line_23_id=self.line23.id,
            line_24_id=self.line24.id,
            line_25_id=self.line25.id,
            line_26_id=self.line26.id,
            line_27_id=self.line27.id,
            line_28_id=self.line28.id,
        )

        xml_encoded_doc2 = b64encode(xml_content2.encode("utf-8"))
        despatch_import = self.DespatchAdviceImport.create(
            {"document": xml_encoded_doc2, "filename": "do_mix2.xml"}
        )
        despatch_import.process_document()

        backorder = self.purchase_order.picking_ids.filtered(lambda p: p.backorder_id)
        initial_pick = self.purchase_order.picking_ids.filtered(
            lambda p: not p.backorder_id
        )

        self.assertEqual(len(backorder), 2)
        self.assertEqual(len(initial_pick), 1)

        po_moves = self.line21.move_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )

        self.assertTrue(po_moves)

        move_for_backorder_pick2 = backorder.move_ids.filtered(
            lambda m: m.product_id.id == self.p24.id
        )

        self.assertEqual(len(move_for_backorder_pick2), 2)
