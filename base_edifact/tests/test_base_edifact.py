# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo.tests.common import TransactionCase
from odoo.tools import file_open


def _get_file_content(filename):
    path = "base_edifact/tests/files/" + filename
    with file_open(path, "rb") as fd:
        return fd.read()


class TestBaseEdifact(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.base_edifact_model = self.env["base.edifact"]

    def tearDown(self):
        return super().tearDown()

    def test_pydifact_obj(self):
        edifact_docu = _get_file_content("Retail_EDIFACT_ORDERS_sample1.txt")
        obj = self.base_edifact_model.pydifact_obj(edifact_docu)
        # [1]: to get the list messages, [0]: to get the first list value of the segments
        self.assertEqual(obj[1]["segments"][0]["BGM"][1], "1AA1TEST")

    def test_map2odoo_address(self):
        """Address segment
        DP. Party to which goods should be delivered, if not identical with
            consignee.
            NAD+DP+5550534000086::9+++++++DE'
            NAD segment: ['DP', ['5550534022101', '', '9'], '', '', '', '', '', '', 'ES']
        """
        seg = ["DP", ["5550534000086", "", "9"], "", "", "", "", "", "", "ES"]
        address = self.base_edifact_model.map2odoo_address(seg)
        self.assertEqual(address["type"], "delivery")
        self.assertEqual(address["partner"], {"gln": "5550534000086"})
        self.assertEqual(address["address"]["country_code"], "ES")

    def test_map2odoo_currency(self):
        seg = ("2", "EUR", "9")
        currency = self.base_edifact_model.map2odoo_currency(seg)
        self.assertEqual(currency["iso"], "EUR")
        self.assertEqual(currency["symbol"], "€")

    def test_map2odoo_product(self):
        seg = ("1", "", ["8885583503464", "EN"])
        product = self.base_edifact_model.map2odoo_product(seg)
        self.assertEqual(product["barcode"], "8885583503464")

    def test_map2odoo_qty(self):
        seg = (["21", "2"],)
        qty = self.base_edifact_model.map2odoo_qty(seg)
        self.assertEqual(qty, 2.0)

    def test_map2odoo_unit_price(self):
        seg = (["AAA", "19.75"],)
        unit_price = self.base_edifact_model.map2odoo_unit_price(seg)
        self.assertEqual(unit_price, 19.75)
