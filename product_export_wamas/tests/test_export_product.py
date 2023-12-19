# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from freezegun import freeze_time

from odoo.tests import common
from odoo.tools import file_open


class TestExportProduct(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "default_code": "0001",
                "name": "The Yellow Chair",
                "detailed_type": "product",
                "weight": 2,
                "standard_price": 10,
                "lst_price": 12,
                "barcode": "555555",
            }
        )

    def test_export_without_telegram(self):
        with self.assertRaisesRegex(
            ValueError, "Please define expected telegram type."
        ):
            self.product._wamas_export()

    @freeze_time("2023-12-21 04:12:51")
    def test_export_without_specific_dict(self):
        exported_data = self.product._wamas_export(telegram_type="ART")
        expected_data = (
            file_open(
                "product_export_wamas/tests/samples/EXPECTED_PRODUCT_1.wamas", "r"
            )
            .read()
            .encode("iso-8859-1")
        )

        self.assertEqual(exported_data, expected_data)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_specific_dict(self):
        specific_dict = {
            "default_code": "0001",
            "name": "The Green Chair",
            "weight": 2,
        }
        exported_data = self.product._wamas_export(
            specific_dict=specific_dict, telegram_type="ART"
        )
        expected_data = (
            file_open(
                "product_export_wamas/tests/samples/EXPECTED_PRODUCT_2.wamas", "r"
            )
            .read()
            .encode("iso-8859-1")
        )
        self.assertEqual(exported_data, expected_data)
