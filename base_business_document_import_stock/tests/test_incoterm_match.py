# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestIncotermMatch(TransactionCase):
    def test_incoterm_match(self):
        bdoo = self.env["business.document.import"]
        incoterm_dict = {"code": "EXW"}
        res = bdoo._match_incoterm(incoterm_dict, [])
        self.assertEquals(res, self.env.ref("account.incoterm_EXW"))
        incoterm_dict = {"code": "EXW WORKS"}
        res = bdoo._match_incoterm(incoterm_dict, [])
        self.assertEquals(res, self.env.ref("account.incoterm_EXW"))
        incoterm_dict = {}
        res = bdoo._match_incoterm(incoterm_dict, [])
        self.assertFalse(res)
