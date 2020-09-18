# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestBaseBusinessDocumentImport(common.SavepointCase):
    def test_match_partner(self):
        externalID = "MYEXTID"
        externalSchemeID = "EXTCATEG"
        partner1 = self.env["res.partner"].create({"name": "Extra ID"})
        categ = self.env["res.partner.id_category"].create(
            {"name": "Extra Categ", "code": externalSchemeID}
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": categ.id,
                "name": externalSchemeID,
                "partner_id": partner1.id,
            }
        )
        bdio = self.env["business.document.import"]
        partner_dict = {"id_number": externalID, "id_schemeID": externalSchemeID}
        warn = []
        res = bdio._match_partner(partner_dict, warn, partner_type=False)
        self.assertEqual(res, partner1)
        self.assertTrue(warn)
