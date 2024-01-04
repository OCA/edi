# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from freezegun import freeze_time

from odoo.tests import common
from odoo.tools import file_open


class TestExportBarcode(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "default_code": "113 113 113",
                "name": "The Yellow Chair",
            }
        )
        cls.barcode = cls.env["product.barcode"].create(
            {
                "name": "256256256",
                "product_id": cls.product.id,
            }
        )

    def test_export_without_telegram(self):
        with self.assertRaisesRegex(
            ValueError, "Please define expected telegram type."
        ):
            self.barcode._wamas_export()

    @freeze_time("2023-12-21 04:12:51")
    def test_export_without_specific_dict(self):
        exported_data = self.barcode._wamas_export(telegram_type="ARTEAN")
        expected_data = (
            file_open(
                "product_export_wamas/tests/samples/EXPECTED_BARCODE_1.wamas", "r"
            )
            .read()
            .encode("iso-8859-1")
        )
        self.assertEqual(exported_data, expected_data)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_specific_dict(self):
        specific_dict = {
            "barcode": "256256256",
            "product": "113 113 113",
        }
        exported_data = self.barcode._wamas_export(
            specific_dict=specific_dict, telegram_type="ARTEAN"
        )
        expected_data = (
            file_open(
                "product_export_wamas/tests/samples/EXPECTED_BARCODE_2.wamas", "r"
            )
            .read()
            .encode("iso-8859-1")
        )
        self.assertEqual(exported_data, expected_data)
