# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from base64 import b64encode

from odoo.tools import file_open

from odoo.addons.despatch_advice_import.tests.common import (
    TestDespatchAdviceImportCommon,
)


class TestDespatchAdviceMix(TestDespatchAdviceImportCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p1 = cls._create_product("CYDECTIN 0,1% ORAL DRENCH 1L", "1354307", "P1")
        cls.p2 = cls._create_product("CYDECTIN TRICLAMOX OVIN 1 L", "10005578", "p2")
        cls.p3 = cls._create_product("VANGUARD DA2PI-CPV 25X1D", "10001458", "p3")
        cls.p4 = cls._create_product("APOQUEL  5,4MG 100CP", "10022152", "p4")
        cls.p5 = cls._create_product("DOGMINTH PATE TUBE 24GR", "10002655", "p5")
        cls.p6 = cls._create_product("RISPOVAL IBR INACT 100ML", "10001112", "p6")
        cls.p7 = cls._create_product("MODERIN 32MG   30CP", "10005211", "p7")
        cls.p8 = cls._create_product("CIDR  1,38gr BOITE DE 10", "10002949", "p8")
        cls.p9 = cls._create_product("VERSICAN+ BB ORAL 10x1d", "10022422", "p9")
        cls.p10 = cls._create_product("VERSICAN+ BBPi IN 10x1d", "10023409", "p10")
        cls.p11 = cls._create_product("CONVENIA SOL INJ 10ml", "10007669", "p11")
        cls.p12 = cls._create_product("WITNESS LH 6x1 TEST", "10012140", "p12")
        cls.p13 = cls._create_product(
            "WITNESS RELAXIN 5x1 TEST GESTATION", "10010958", "p13"
        )
        cls.p14 = cls._create_product("ACEGON 10x6ML", "10010146", "p14")
        cls.p15 = cls._create_product("EQUEST GEL ORAL 700kg", "10009831", "p15")
        cls.p16 = cls._create_product("WITNESS GIARDIA 5 TESTS", "10009407", "p16")
        cls.p17 = cls._create_product("CATMINTH PATE SERINGUE 3GR", "10003022", "p17")
        cls.p18 = cls._create_product("FENDOV 1250 12 BOLI", "10006920", "p18")
        cls.p19 = cls._create_product("FEVAXYN PENTOFEL 10X1D", "10004344", "p19")
        cls.p20 = cls._create_product("VANGUARD CPV-LEPTO 25x1D", "10001455", "p20")
        cls.p21 = cls._create_product(
            "VANGUARD DA2PI-CPV-LEPTO 25x1D (7)", "10001457", "p21"
        )
        cls.p22 = cls._create_product("VANGUARD LEPTO 25x1D", "10001459", "p22")
        cls.p23 = cls._create_product("VERSICAN+ DHPPI 25x1d", "10011717", "p23")
        cls.p24 = cls._create_product("VERSICAN+ DHPPI/L4 25x1d", "10011718", "p24")
        cls.p25 = cls._create_product("VERSICAN+ L4 25x1d", "10011728", "p25")
        cls.p26 = cls._create_product("VERSICAN+ PI 25x1d", "10011736", "p26")
        cls.p27 = cls._create_product("VERSIFEL FELV 25x1d", "10009541", "p27")
        cls.p28 = cls._create_product("VERSIGUARD RABIES 10x1d", "10016049", "p28")
        cls.p29 = cls._create_product("WITNESS FELV-FIV 10x1 TEST", "10009061", "p29")
        cls.p30 = cls._create_product("WITNESS FELV-FIV 5x1 TEST", "10006252", "p30")
        cls.purchase_order = cls._create_purchase_order(
            [
                cls._get_po_line_vals(cls.p1, 60, 51.4),
                cls._get_po_line_vals(cls.p2, 40, 78.65),
                cls._get_po_line_vals(cls.p3, 24, 96.32),
                cls._get_po_line_vals(cls.p4, 96, 73.86),
                cls._get_po_line_vals(cls.p5, 280, 7.2),
                cls._get_po_line_vals(cls.p6, 20, 114.36),
                cls._get_po_line_vals(cls.p7, 10, 47.62),
                cls._get_po_line_vals(cls.p8, 40, 116.83),
                cls._get_po_line_vals(cls.p9, 20, 93.08),
                cls._get_po_line_vals(cls.p10, 20, 97.68),
                cls._get_po_line_vals(cls.p11, 120, 150.27),
                cls._get_po_line_vals(cls.p12, 1, 134.32),
                cls._get_po_line_vals(cls.p13, 2, 92.37),
                cls._get_po_line_vals(cls.p14, 4, 99.13),
                cls._get_po_line_vals(cls.p15, 480, 16.62),
                cls._get_po_line_vals(cls.p16, 1, 58.12),
                cls._get_po_line_vals(cls.p17, 400, 6.07),
                cls._get_po_line_vals(cls.p18, 30, 232.56),
                cls._get_po_line_vals(cls.p19, 160, 164.05),
                cls._get_po_line_vals(cls.p20, 5, 88.73),
                cls._get_po_line_vals(cls.p21, 30, 123.60),
                cls._get_po_line_vals(cls.p22, 10, 37.79),
                cls._get_po_line_vals(cls.p23, 30, 94.93),
                cls._get_po_line_vals(cls.p24, 200, 156.90),
                cls._get_po_line_vals(cls.p25, 60, 65.41),
                cls._get_po_line_vals(cls.p26, 40, 53.73),
                cls._get_po_line_vals(cls.p27, 15, 277.55),
                cls._get_po_line_vals(cls.p28, 30, 24.14),
                cls._get_po_line_vals(cls.p29, 2, 154.00),
                cls._get_po_line_vals(cls.p30, 2, 80.87),
            ]
        )
        for i, line in enumerate(cls.purchase_order.order_line, 1):
            setattr(cls, f"line{i}", line)
        cls.purchase_order.button_confirm()
        cls.picking = cls.purchase_order.picking_ids
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
            picking_name="0810805774",
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
