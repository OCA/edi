# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestBaseBusinessDocumentImport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        externalID = "MYEXTID"
        externalSchemeID = "EXTCATEG"
        cls.partner1 = cls.env["res.partner"].create({"name": "Extra ID"})
        categ = cls.env["res.partner.id_category"].create(
            {"name": "Extra Categ", "code": externalSchemeID}
        )
        cls.env["res.partner.id_number"].create(
            {
                "category_id": categ.id,
                "name": externalID,
                "partner_id": cls.partner1.id,
            }
        )
        cls.partner1_contact = cls.env["res.partner"].create(
            {"name": "Contact", "parent_id": cls.partner1.id, "type": "contact"}
        )
        cls.partner_dict = {
            "id_number": [{"value": externalID, "schemeID": externalSchemeID}]
        }

    def test_match_partner(self):
        bdio = self.env["business.document.import"]
        warn = []
        res = bdio._match_partner(self.partner_dict, warn, partner_type=False)
        self.assertEqual(res, self.partner1)

    def test_match_partner_contact(self):
        bdio = self.env["business.document.import"]
        warn = []
        # Match contact
        self.partner_dict["contact"] = "Contact"
        res = bdio._match_partner(self.partner_dict, warn, partner_type=False)
        self.assertEqual(res, self.partner1_contact)
        # Match partner
        self.partner_dict["contact"] = "Contact2"
        res = bdio._match_partner(self.partner_dict, warn, partner_type=False)
        self.assertEqual(res, self.partner1)
