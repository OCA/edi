# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from freezegun import freeze_time

from odoo.tests import common
from odoo.tools import file_open


class TestExportPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "ref": "0001",
                "name": "Adam Smith",
                "street2": "",
                "zip": "79782",
                "city": "Sand Springs",
                "phone": "432-393-1264",
                "email": "aaa",
                "street": "adam@dayrep.com",
            }
        )

    def test_export_without_telegram(self):
        with self.assertRaisesRegex(ValueError, "Need telegram for exporting"):
            self.partner._wamas_export()

    @freeze_time("2023-12-21 04:12:51")
    def test_export_without_specific_dict(self):
        exported_data = self.partner._wamas_export(telegram="LST")
        expected_data = (
            file_open("partner_export_wamas/tests/samples/EXPECTED_DATA1.wamas", "r")
            .read()
            .encode("iso-8859-1")
        )
        self.assertEqual(exported_data, expected_data)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_specific_dict(self):
        specific_dict = {
            "ref": "113",
            "name": "Thomas",
            "street": "223 Main St",
            "email": "testing@example.com",
        }
        exported_data = self.partner._wamas_export(
            specific_dict=specific_dict, telegram="LST"
        )
        expected_data = (
            file_open("partner_export_wamas/tests/samples/EXPECTED_DATA2.wamas", "r")
            .read()
            .encode("iso-8859-1")
        )
        self.assertEqual(exported_data, expected_data)
