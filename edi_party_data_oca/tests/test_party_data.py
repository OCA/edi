# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentTestCase

from ..utils import get_party_data_component


class PartyDataTestCase(EDIBackendCommonComponentTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("edi_oca.demo_edi_backend")
        cls.cat_model = cls.env["res.partner.id_category"]
        cls.all_cat = cls.cat_model.browse()
        for i in range(1, 4):
            rec = cls.cat_model.create({"code": f"cat{i}", "name": f"Cat {i}"})
            cls.all_cat += rec
            setattr(cls, f"category{i}", rec)
        for i in range(1, 4):
            rec = cls.env["res.partner"].create(
                {
                    "name": f"Test Partner {i}",
                    "id_numbers": [
                        (
                            0,
                            0,
                            {
                                "name": f"{cat.code}-p{i}",
                                "category_id": cat.id,
                            },
                        )
                        for cat in cls.all_cat[i - 1 :]
                    ],
                }
            )
            setattr(cls, f"partner{i}", rec)

        # No need for special file name gen
        cls.exc_type = cls._create_exchange_type(
            name="ID output test",
            code="id_out_test",
            direction="output",
        )
        cls.exc_record = cls.backend.create_record("id_out_test", {})

    def _get_provider(self, partner):
        return get_party_data_component(self.exc_record, partner)

    def _make_expected_data(self, partner, number, allowed_codes=None, **kw):
        data = {
            "name": partner.name,
            "identifiers": [
                {"attrs": {"schemeID": "cat1"}, "value": f"cat1-p{number}"},
                {"attrs": {"schemeID": "cat2"}, "value": f"cat2-p{number}"},
                {"attrs": {"schemeID": "cat3"}, "value": f"cat3-p{number}"},
            ],
            "endpoint": {},
        }
        data.update(kw)
        if allowed_codes:
            data["identifiers"] = [
                x
                for x in data["identifiers"]
                if x["attrs"]["schemeID"] in allowed_codes
            ]
        return data

    def test_lookup(self):
        provider = self._get_provider(self.partner1)
        self.assertEqual(provider.partner, self.partner1)
        self.assertFalse(provider.allowed_id_categories)

    def test_data(self):
        expected = (
            (self.partner1, self._make_expected_data(self.partner1, 1)),
            (
                self.partner2,
                self._make_expected_data(
                    self.partner2, 2, allowed_codes=["cat2", "cat3"]
                ),
            ),
            (
                self.partner3,
                self._make_expected_data(self.partner3, 3, allowed_codes=["cat3"]),
            ),
        )
        for partner, expected_data in expected:
            provider = self._get_provider(partner)
            res = provider.get_party()
            self.assertEqual(res, expected_data)

    def test_data_limited_1(self):
        self.exc_type.id_category_ids = self.category1
        expected = (
            (
                self.partner1,
                self._make_expected_data(self.partner1, 1, allowed_codes=["cat1"]),
            ),
            (self.partner2, self._make_expected_data(self.partner2, 2, identifiers=[])),
            (self.partner3, self._make_expected_data(self.partner3, 3, identifiers=[])),
        )
        for partner, expected_data in expected:
            provider = self._get_provider(partner)
            res = provider.get_party()
            self.assertEqual(res, expected_data)

    def test_data_limited_2(self):
        self.exc_type.id_category_ids = self.category2
        expected = (
            (
                self.partner1,
                self._make_expected_data(self.partner1, 1, allowed_codes=["cat2"]),
            ),
            (
                self.partner2,
                self._make_expected_data(self.partner2, 2, allowed_codes=["cat2"]),
            ),
            (self.partner3, self._make_expected_data(self.partner3, 3, identifiers=[])),
        )
        for partner, expected_data in expected:
            provider = self._get_provider(partner)
            res = provider.get_party()
            self.assertEqual(res, expected_data)

    def test_data_limited_3(self):
        self.exc_type.id_category_ids = self.category3
        expected = (
            (
                self.partner1,
                self._make_expected_data(self.partner1, 1, allowed_codes=["cat3"]),
            ),
            (
                self.partner2,
                self._make_expected_data(self.partner2, 2, allowed_codes=["cat3"]),
            ),
            (
                self.partner3,
                self._make_expected_data(self.partner3, 3, allowed_codes=["cat3"]),
            ),
        )
        for partner, expected_data in expected:
            provider = self._get_provider(partner)
            res = provider.get_party()
            self.assertEqual(res, expected_data)
