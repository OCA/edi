# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestBaseBusinessDocumentImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Account = cls.env["account.account"]
        cls.AccountTax = cls.env["account.tax"]
        cls.bdio = cls.env["business.document.import"]
        cls.Partner = cls.env["res.partner"]
        cls.PartnerBank = cls.env["res.partner.bank"]
        cls.Product = cls.env["product.product"]
        cls.France = cls.env.ref("base.fr")
        cls.usd = cls.env.ref("base.USD")
        cls.eur = cls.env.ref("base.EUR")
        cls.krw = cls.env.ref("base.KRW")
        cls.vat_tax_type = cls.env.ref("account_tax_unece.tax_type_vat")
        cls.s_tax_categ = cls.env.ref("account_tax_unece.tax_categ_s")
        cls.service_product = cls.Product.create(
            {
                "name": "Virtual Interior Design",
                "type": "service",
                "uom_id": cls.env.ref("uom.product_uom_hour").id,
            }
        )
        cls.consu_product = cls.Product.create(
            {
                "name": "Office Chair",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "default_code": "FURN_77779",
            }
        )
        cls.partner_acme_corp = cls.Partner.create(
            {
                "name": "Acme Corporation",
                "email": "acme_corp@yourcompany.example.com",
                "is_company": True,
            }
        )
        cls.cash_basis_transfer_account = cls.Account.create(
            {
                "code": "cash.basis.transfer.account",
                "name": "cash_basis_transfer_account",
                "account_type": "income",
                "reconcile": True,
            }
        )
        cls.pound = cls.env["uom.uom"].create(
            {
                "name": "pnd",
                "relative_factor": 454,
                "relative_uom_id": cls.env.ref("uom.product_uom_gram").id,
            }
        )

    def test_match_partner(self):
        partner1 = self.Partner.create(
            {"name": "COGIP", "ref": "COGIP", "website": "http://example.com/"}
        )
        partner_ready_mat = self.Partner.create(
            {
                "name": "Ready Match",
                "is_company": True,
                "email": "ready.mat28@example.com",
            }
        )
        # match on domain extracted from email with warning
        partner_dict = {"email": "alexis.delattre@example.com"}
        warn = []
        res = self.bdio._match_partner(partner_dict, warn, partner_type=False)
        self.assertEqual(res, partner1)
        self.assertTrue(warn)
        partner_dict = {"name": "ready match "}
        partner_ready_mat.supplier_rank = 1  # to be considered as a supplier
        res = self.bdio._match_partner(partner_dict, [], partner_type="supplier")
        self.assertEqual(res, partner_ready_mat)
        partner_dict = {"ref": "COGIP"}
        res = self.bdio._match_partner(partner_dict, [], partner_type=False)
        self.assertEqual(res, partner1)

    def test_direct_match_recordset(self):
        partner = self.Partner.create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        partner_dict = {
            "recordset": partner,
        }
        partner_match = self.bdio._direct_match(partner_dict, self.Partner, True)
        self.assertEqual(partner, partner_match)

        with self.assertRaises(UserError):
            self.bdio._direct_match(partner_dict, self.PartnerBank, True)

        partner_match = self.bdio._direct_match(partner_dict, self.PartnerBank, False)
        self.assertEqual(None, partner_match)

    def test_direct_match_id(self):
        partner = self.Partner.create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        partner_dict = {
            "id": partner.id,
        }
        partner_match = self.bdio._direct_match(partner_dict, self.Partner, True)
        self.assertEqual(partner, partner_match)

        partner_dict = {
            "id": 234234234234231,
        }
        with self.assertRaises(UserError):
            self.bdio._direct_match(partner_dict, self.Partner, True)

    def test_direct_match_xmlid(self):
        partner_dict = {
            "xmlid": "i.dont.exist.odoo",
        }
        with self.assertRaises(UserError):
            self.bdio._direct_match(partner_dict, self.Partner, True)

        partner_dict = {
            "xmlid": "base.fr",
        }
        with self.assertRaises(UserError):
            self.bdio._direct_match(partner_dict, self.Partner, True)

        partner_dict = {
            "xmlid": "base.main_partner",
        }
        partner = self.bdio._direct_match(partner_dict, self.Partner, True)
        self.assertEqual(partner.id, self.env.ref("base.main_partner").id)

    def test_match_partner_ref(self):
        partner1 = self.Partner.create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        partner_dict = {
            "name": "Alexis Delattre",
            "email": "alexis.delattre@example.com",
            "ref": "C1242",
        }
        chatter_msg = []
        domain = []
        order = ""
        partner = self.bdio._match_partner_ref(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner1)

    def test_match_partner_contact(self):
        partner_email = self.Partner.create(
            {
                "email": "alexis.email@example.com",
                "name": "Alexis email",
            }
        )
        partner_contact = self.Partner.create(
            {
                "email": "alexis.name@example.com",
                "name": "Alexis name",
            }
        )
        partner_phone = self.Partner.create(
            {
                "email": "alexis.phone@example.com",
                "phone": "01.41.98.12.42",
                "name": "Alexis phone",
            }
        )
        chatter_msg = []
        domain = []
        order = ""

        partner_dict = {
            "name": "Alexis email",
            "email": "alexis.email@example.com",
        }
        partner = self.bdio._match_partner_contact(
            partner_dict, chatter_msg, domain, order
        )
        self.assertEqual(partner, partner_email)

        partner_dict = {
            "contact": "Alexis name",
            "email": "alexis.name@example.com",
        }
        partner = self.bdio._match_partner_contact(
            partner_dict, chatter_msg, domain, order
        )
        self.assertEqual(partner, partner_contact)

        partner_dict = {
            "name": "Alexis phone",
            "email": "alexis.phone@example.com",
            "phone": "01.41.98.12.42",
        }
        partner = self.bdio._match_partner_contact(
            partner_dict, chatter_msg, domain, order
        )
        self.assertEqual(partner, partner_phone)

    def test_match_partner_name(self):
        partner_name = self.Partner.create(
            {
                "email": "alexis.name@example.com",
                "name": "Alexis name",
            }
        )
        chatter_msg = []
        domain = []
        order = ""

        partner_dict = {
            "name": "Alexis name",
            "email": "alexis.name@example.com",
        }
        partner = self.bdio._match_partner_name(
            partner_dict, chatter_msg, domain, order
        )
        self.assertEqual(partner, partner_name)

    def test_get_partner_website_domain(self):
        www_website = {"website": "www.example.com"}
        website_domain = self.bdio._get_partner_website_domain(www_website)
        self.assertEqual(website_domain, "example.com")

        no_website = self.bdio._get_partner_website_domain({})
        self.assertEqual(False, no_website)

        https_www_website = {"website": "https://www.example.com"}
        website_domain = self.bdio._get_partner_website_domain(https_www_website)
        self.assertEqual(website_domain, "example.com")

        https_website = {"website": "https://example.com"}
        website_domain = self.bdio._get_partner_website_domain(https_website)
        self.assertEqual(website_domain, "example.com")

        https_path_website = {"website": "https://subdomain.example.com/bla/bla"}
        website_domain = self.bdio._get_partner_website_domain(https_path_website)
        self.assertEqual(website_domain, "example.com")

        https_big_subdomain_website = {
            "website": "https://just.a.big.subdomain.example.com"
        }
        website_domain = self.bdio._get_partner_website_domain(
            https_big_subdomain_website
        )
        self.assertEqual(website_domain, "example.com")

    def test_match_shipping_partner(self):
        partner1 = self.Partner.create(
            {
                "name": "Akretion France",
                "street": "27 rue Henri Rolland",
                "zip": "69100",
                "country_id": self.France.id,
                "email": "contact@akretion.com",
            }
        )
        self.Partner.create(
            {
                "parent_id": partner1.id,
                "name": "Sébastien BEAU",
                "email": "sebastien.beau@akretion.com",
                "type": "contact",
            }
        )
        cpartner3 = self.Partner.create(
            {
                "parent_id": partner1.id,
                "name": "Flo",
                "email": "flo@akretion.com",
                "street": "42 rue des lilas d'Espagne",
                "zip": "92400",
                "city": "Courbevoie",
                "country_id": self.France.id,
                "type": "invoice",
            }
        )
        shipping_dict = {
            "email": "contact@akretion.com",
        }
        res = self.bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, partner1)
        shipping_dict = {
            "street": "42 rue des lilas d'Espagne",
            "zip": "92400",
            "country_code": "fr",
        }
        res = self.bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, cpartner3)
        shipping_dict["zip"] = "92500"
        with self.assertRaises(UserError):
            self.bdio._match_shipping_partner(shipping_dict, None, [])

        no_error = self.bdio._match_shipping_partner(
            shipping_dict, None, [], raise_exception=False
        )
        self.assertEqual(no_error, None)

        partner2 = self.Partner.create(
            {
                "name": "Alex Corp",
                "zip": "69009",
                "country_id": self.France.id,
                "email": "contact@alex.com",
            }
        )
        shipping_dict = {
            "email": "contact@alex.com",
            "zip": "69009",
            "country_code": "FR",
        }
        res = self.bdio._match_shipping_partner(shipping_dict, None, [])
        self.assertEqual(res, partner2)

    def test_match_currency(self):
        currency_dict = {"xmlid": "base.USD"}
        res = self.bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.usd)
        first_cur = self.env["res.currency"].search([], limit=1)
        currency_dict = {"id": first_cur.id}
        res = self.bdio._match_currency(currency_dict, [])
        self.assertEqual(res, first_cur)
        currency_dict = {"recordset": first_cur}
        res = self.bdio._match_currency(currency_dict, [])
        self.assertEqual(res, first_cur)
        currency_dict = {"iso": "EUR"}
        res = self.bdio.with_context(active_test=False)._match_currency(
            currency_dict, []
        )
        self.assertEqual(res, self.eur)
        currency_dict = {"symbol": "€"}
        res = self.bdio.with_context(active_test=False)._match_currency(
            currency_dict, []
        )
        self.assertEqual(res, self.eur)
        currency_dict = {"country_code": "fr "}
        res = self.bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.eur)
        currency_dict = {"iso_or_symbol": "€"}
        res = self.bdio.with_context(active_test=False)._match_currency(
            currency_dict, []
        )
        self.assertEqual(res, self.eur)
        currency_id = self.krw.id
        self.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = 1", (currency_id,)
        )
        currency_dict = {}
        res = self.bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.krw)

    def test_match_product(self):
        ppo = self.Product
        product1 = ppo.create(
            {
                "name": "Test Product",
                "barcode": "9782203121102",
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner_acme_corp.id,
                            "product_code": "TEST1242",
                        },
                    ),
                ],
            }
        )
        # Match by code
        product_dict = {"code": "FURN_77779 "}
        res = self.bdio._match_product(product_dict, [])
        self.assertEqual(res, self.consu_product)
        # Match by barcode
        product_dict = {"barcode": "9782203121102"}
        res = self.bdio._match_product(product_dict, [])
        self.assertEqual(res, product1)

        # Match by seller
        product_dict = {"code": "TEST1242"}
        res = self.bdio._match_product(
            product_dict, [], seller=self.partner_acme_corp.id
        )
        self.assertEqual(res, product1)

        raise_test = True
        try:
            self.bdio._match_product(product_dict, [], seller=False)
            raise_test = False
        except Exception:
            logger.info("Exception catched.")

        self.assertTrue(raise_test)

    def test_match_uom(self):
        uom_dict = {"unece_code": "KGM"}
        res = self.bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_kgm"))
        uom_dict = {"unece_code": "NIU"}
        res = self.bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_unit"))
        uom_dict = {"name": "day"}
        res = self.bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_day"))
        uom_dict = {"name": "pnd"}
        res = self.bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.pound)
        uom_dict = {}
        product = self.service_product
        res = self.bdio._match_uom(uom_dict, [], product=product)
        self.assertEqual(res, product.uom_id)

    def test_match_tax(self):
        # on purpose, I use a rate that doesn't exist
        # so that this test works even if the l10n_de is installed
        de_tax_21 = self.AccountTax.create(
            {
                "name": "German VAT purchase 18.0%",
                "description": "DE-VAT-buy-18.0",
                "type_tax_use": "purchase",
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": self.vat_tax_type.id,
                "unece_categ_id": self.s_tax_categ.id,
            }
        )
        de_tax_21_onpayment = self.AccountTax.create(
            {
                "name": "German VAT purchase 18.0% (On Payment)",
                "description": "DE-VAT-buy-18.0",
                "type_tax_use": "purchase",
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_payment",
                "unece_type_id": self.vat_tax_type.id,
                "unece_categ_id": self.s_tax_categ.id,
                "cash_basis_transition_account_id": self.cash_basis_transfer_account.id,
            }
        )
        de_tax_21_ttc = self.AccountTax.create(
            {
                "name": "German VAT purchase 18.0% TTC",
                "description": "DE-VAT-buy-18.0-TTC",
                "type_tax_use": "purchase",
                "price_include_override": "tax_included",
                "amount": 18,
                "amount_type": "percent",
                "tax_exigibility": "on_invoice",
                "unece_type_id": self.vat_tax_type.id,
                "unece_categ_id": self.s_tax_categ.id,
            }
        )
        tax_dict = {
            "amount_type": "percent",
            "amount": 18,
            "unece_type_code": "VAT",
            "unece_categ_code": "S",
            "unece_due_date_code": "5",
        }
        res = self.bdio._match_tax(tax_dict, [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        tax_dict.pop("unece_categ_code")
        res = self.bdio._match_tax(tax_dict, [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        res = self.bdio._match_tax(
            tax_dict, [], type_tax_use="purchase", price_include=True
        )
        self.assertEqual(res, de_tax_21_ttc)
        res = self.bdio._match_taxes([tax_dict], [], type_tax_use="purchase")
        self.assertEqual(res, de_tax_21)
        res = self.bdio._match_taxes(
            [dict(tax_dict, unece_due_date_code=72)], [], type_tax_use="purchase"
        )
        self.assertEqual(res, de_tax_21_onpayment)

    def test_match_account_exact(self):
        acc = self.Account.create(
            {
                "name": "Test 898999",
                "code": "898999",
                "account_type": "expense",
            }
        )
        res = self.bdio._match_account({"code": "898999"}, [])
        self.assertEqual(acc, res)

    def test_match_account_bigger_in(self):
        acc = self.Account.create(
            {
                "name": "Test 898999",
                "code": "898999",
                "account_type": "expense",
            }
        )
        res = self.bdio._match_account({"code": "89899900"}, [])
        self.assertEqual(acc, res)

    def test_match_account_smaller_in(self):
        acc = self.Account.create(
            {
                "name": "Test 89899910",
                "code": "89899910",
                "account_type": "expense",
            }
        )
        chatter = []
        res = self.bdio._match_account({"code": "898999"}, chatter)
        self.assertEqual(acc, res)
        self.assertEqual(len(chatter), 1)
