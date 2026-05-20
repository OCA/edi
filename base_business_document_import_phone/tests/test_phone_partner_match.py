# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestPhonePartnerMatch(TransactionCase):
    def test_phone_partner_match(self):
        rpo = self.env["res.partner"]
        bdoo = self.env["business.document.import"]
        partner = rpo.create(
            {
                "name": "Test partner",
                "country_id": self.env.ref("base.fr").id,
                "phone": "01 41 98 12 42",
                "supplier_rank": 10,
            }
        )
        partner._onchange_phone_validation()
        self.assertEqual(partner.phone, "+33 1 41 98 12 42")
        partner_dict = {
            "country_code": "FR",
            "phone": "01.41.98.12.42",
        }
        res = bdoo._match_partner(partner_dict, [])
        self.assertEqual(res, partner)
        partner = rpo.create(
            {
                "name": "Test partner mobile",
                "country_id": self.env.ref("base.fr").id,
                "phone": "+33699887766",
                "supplier_rank": 10,
            }
        )
        partner._onchange_phone_validation()
        partner_dict = {
            "country_code": "FR",
            "phone": "(0)6-99-88-77-66",
        }
        res = bdoo._match_partner(partner_dict, [])
        self.assertEqual(res, partner)
