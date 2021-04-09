# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBaseBusinessDocumentImport(TransactionCase):
    def test_match_partner(self):
        partner1 = self.env["res.partner"].create(
            {"name": "COGIP", "ref": "COGIP", "website": "http://example.com/"}
        )
        bdio = self.env["business.document.import"]
        # match on domain extracted from email with warning
        partner_dict = {"email": "alexis.delattre@example.com"}
        warn = []
        res = bdio._match_partner(partner_dict, warn, partner_type=False)
        self.assertEqual(res, partner1)
        self.assertTrue(warn)
        partner_dict = {"name": "ready mat "}
        partner_ready_mat = self.env.ref("base.res_partner_4")
        partner_ready_mat.supplier_rank = 1  # to be considered as a supplier
        res = bdio._match_partner(partner_dict, [], partner_type="supplier")
        self.assertEqual(res, partner_ready_mat)
        partner_dict = {"ref": "COGIP"}
        res = bdio._match_partner(partner_dict, [], partner_type=False)
        self.assertEqual(res, partner1)

    def test_match_shipping_partner(self):
        rpo = self.env["res.partner"]
        bdio = self.env["business.document.import"]
        partner1 = rpo.create(
            {
                "name": "Akretion France",
                "street": "27 rue Henri Rolland",
                "zip": "69100",
                "country_id": self.env.ref("base.fr").id,
                "email": "contact@akretion.com",
            }
        )
        rpo.create(
            {
                "parent_id": partner1.id,
                "name": "Sébastien BEAU",
                "email": "sebastien.beau@akretion.com",
                "type": "contact",
            }
        )
        cpartner3 = rpo.create(
            {
                "parent_id": partner1.id,
                "name": "Flo",
                "email": "flo@akretion.com",
                "street": "42 rue des lilas d'Espagne",
                "zip": "92400",
                "city": "Courbevoie",
                "country_id": self.env.ref("base.fr").id,
                "type": "invoice",
            }
        )
        shipping_dict = {
            "email": "contact@akretion.com",
        }
        res = bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, partner1)
        shipping_dict = {
            "street": "42 rue des lilas d'Espagne",
            "zip": "92400",
            "country_code": "fr",
        }
        res = bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, cpartner3)
        shipping_dict["zip"] = "92500"
        with self.assertRaises(UserError):
            bdio._match_shipping_partner(shipping_dict, None, [])
        partner2 = rpo.create(
            {
                "name": "Alex Corp",
                "zip": "69009",
                "country_id": self.env.ref("base.fr").id,
                "email": "contact@alex.com",
            }
        )
        shipping_dict = {
            "email": "contact@alex.com",
            "zip": "69009",
            "country_code": "FR",
        }
        res = bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, partner2)

    def test_match_currency(self):
        bdio = self.env["business.document.import"]
        currency_dict = {"iso": "EUR"}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.EUR"))
        currency_dict = {"symbol": "€"}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.EUR"))
        currency_dict = {"country_code": "fr "}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.EUR"))
        currency_dict = {"iso_or_symbol": "€"}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.EUR"))
        currency_id = self.env.ref("base.KRW").id
        self.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = 1", (currency_id,)
        )
        currency_dict = {}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.KRW"))

    def test_match_product(self):
        bdio = self.env["business.document.import"]
        ppo = self.env["product.product"]
        product1 = ppo.create(
            {
                "name": "Test Product",
                "barcode": "9782203121102",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.env.ref("base.res_partner_2").id,
                            "product_code": "TEST1242",
                        },
                    ),
                ],
            }
        )
        product_dict = {"code": "FURN_7777 "}
        res = bdio._match_product(product_dict, [])
        self.assertEqual(res, self.env.ref("product.product_delivery_01"))
        product_dict = {"barcode": "9782203121102"}
        res = bdio._match_product(product_dict, [])
        self.assertEqual(res, product1)
        product_dict = {"code": "TEST1242"}
        res = bdio._match_product(
            product_dict, [], seller=self.env.ref("base.res_partner_2")
        )
        self.assertEqual(res, product1)
        raise_test = True
        try:
            bdio._match_product(product_dict, [], seller=False)
            raise_test = False
        except Exception:
            pass
        self.assertTrue(raise_test)

    def test_match_uom(self):
        bdio = self.env["business.document.import"]
        uom_dict = {"unece_code": "KGM"}
        res = bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_kgm"))
        uom_dict = {"unece_code": "NIU"}
        res = bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_unit"))
        uom_dict = {"name": "day"}
        res = bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_day"))
        uom_dict = {"name": "L"}
        res = bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_litre"))
        uom_dict = {}
        product = self.env.ref("product.product_product_1")
        res = bdio._match_uom(uom_dict, [], product=product)
        self.assertEqual(res, product.uom_id)

    def test_match_tax(self):
        # on purpose, I use a rate that doesn't exist
        # so that this test works even if the l10n_de is installed
        de_tax_21 = self.env["account.tax"].create(
            {
                "name": "German VAT purchase 18.0%",
                "description": "DE-VAT-buy-18.0",
                "type_tax_use": "purchase",
                "price_include": False,
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": self.env.ref("account_tax_unece.tax_type_vat").id,
                "unece_categ_id": self.env.ref("account_tax_unece.tax_categ_s").id,
            }
        )
        de_tax_21_onpayment = self.env["account.tax"].create(
            {
                "name": "German VAT purchase 18.0%",
                "description": "DE-VAT-buy-18.0",
                "type_tax_use": "purchase",
                "price_include": False,
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_payment",
                "unece_type_id": self.env.ref("account_tax_unece.tax_type_vat").id,
                "unece_categ_id": self.env.ref("account_tax_unece.tax_categ_s").id,
            }
        )
        de_tax_21_ttc = self.env["account.tax"].create(
            {
                "name": "German VAT purchase 18.0% TTC",
                "description": "DE-VAT-buy-18.0-TTC",
                "type_tax_use": "purchase",
                "price_include": True,
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": self.env.ref("account_tax_unece.tax_type_vat").id,
                "unece_categ_id": self.env.ref("account_tax_unece.tax_categ_s").id,
            }
        )
        bdio = self.env["business.document.import"]
        tax_dict = {
            "amount_type": "percent",
            "amount": 18,
            "unece_type_code": "VAT",
            "unece_categ_code": "S",
            "unece_due_date_code": "5",
        }
        res = bdio._match_tax(tax_dict, [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        tax_dict.pop("unece_categ_code")
        res = bdio._match_tax(tax_dict, [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        res = bdio._match_tax(tax_dict, [], type_tax_use="purchase", price_include=True)
        self.assertEqual(res, de_tax_21_ttc)
        res = bdio._match_taxes([tax_dict], [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        res = bdio._match_taxes(
            [dict(tax_dict, unece_due_date_code=72)], [], type_tax_use="purchase"
        )
        self.assertEqual(res, de_tax_21_onpayment)

    def test_match_account_exact(self):
        bdio = self.env["business.document.import"]
        acc = self.env["account.account"].create(
            {
                "name": "Test 898999",
                "code": "898999",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
            }
        )
        res = bdio._match_account({"code": "898999"}, [])
        self.assertEqual(acc, res)

    def test_match_account_bigger_in(self):
        bdio = self.env["business.document.import"]
        acc = self.env["account.account"].create(
            {
                "name": "Test 898999",
                "code": "898999",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
            }
        )
        res = bdio._match_account({"code": "89899900"}, [])
        self.assertEqual(acc, res)

    def test_match_account_smaller_in(self):
        bdio = self.env["business.document.import"]
        acc = self.env["account.account"].create(
            {
                "name": "Test 89899910",
                "code": "89899910",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
            }
        )
        chatter = []
        res = bdio._match_account({"code": "898999"}, chatter)
        self.assertEqual(acc, res)
        self.assertEqual(len(chatter), 1)
