# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentTestCase
from odoo.addons.edi_party_data_oca.utils import get_party_data_component


class PartyDataTestCase(EDIBackendCommonComponentTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_ubl = cls.env.ref("edi_ubl_oca.edi_backend_ubl_demo")
        cls.backend_no_ubl = cls.env.ref("edi_oca.demo_edi_backend")
        cls.exc_type = cls._create_exchange_type(
            name="UBL output test",
            code="ubl_out_test",
            direction="output",
            backend_id=cls.backend_ubl.id,
            backend_type_id=cls.backend_ubl.backend_type_id.id,
        )
        cls.exc_record_ubl = cls.backend_ubl.create_record("ubl_out_test", {})
        cls.partner = cls.env["res.partner"].create({"name": "UBL Test"})
        cls.exc_record_no_ubl = cls.backend_no_ubl.create_record(
            "test_csv_output", {"model": cls.partner._name, "res_id": cls.partner.id}
        )

    def test_lookup_default(self):
        provider = get_party_data_component(self.exc_record_no_ubl, self.partner)
        self.assertEqual(provider._name, "edi.party.data")
        self.assertEqual(provider.partner, self.partner)
        self.assertFalse(provider.allowed_id_categories)

    def test_lookup_ubl(self):
        provider = get_party_data_component(self.exc_record_ubl, self.partner)
        self.assertEqual(provider._name, "edi.party.data.ubl")
        self.assertEqual(provider.partner, self.partner)
        self.assertFalse(provider.allowed_id_categories)
