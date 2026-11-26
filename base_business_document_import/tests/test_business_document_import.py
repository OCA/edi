# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)


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

    def test_direct_match_recordset(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        partner_dict = {
            "recordset": partner,
        }
        bdio = self.env["business.document.import"]
        partner_match = bdio._direct_match(partner_dict, self.env["res.partner"], True)
        self.assertEqual(partner, partner_match)

        with self.assertRaises(UserError):
            bdio._direct_match(partner_dict, self.env["res.partner.bank"], True)

        partner_match = bdio._direct_match(
            partner_dict, self.env["res.partner.bank"], False
        )
        self.assertEqual(None, partner_match)

    def test_direct_match_id(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        partner_dict = {
            "id": partner.id,
        }
        bdio = self.env["business.document.import"]
        partner_match = bdio._direct_match(partner_dict, self.env["res.partner"], True)
        self.assertEqual(partner, partner_match)

        partner_dict = {
            "id": 234234234234231,
        }
        with self.assertRaises(UserError):
            bdio._direct_match(partner_dict, self.env["res.partner"], True)

    def test_direct_match_xmlid(self):
        partner_dict = {
            "xmlid": "i.dont.exist.odoo",
        }
        bdio = self.env["business.document.import"]
        with self.assertRaises(UserError):
            bdio._direct_match(partner_dict, self.env["res.partner"], True)

        partner_dict = {
            "xmlid": "base.fr",
        }
        with self.assertRaises(UserError):
            bdio._direct_match(partner_dict, self.env["res.partner"], True)

        partner_dict = {
            "xmlid": "base.main_partner",
        }
        partner = bdio._direct_match(partner_dict, self.env["res.partner"], True)
        self.assertEqual(partner.id, self.env.ref("base.main_partner").id)

    def test_match_partner_ref(self):
        partner1 = self.env["res.partner"].create(
            {
                "name": "Alexis Delattre",
                "email": "alexis.delattre@example.com",
                "ref": "C1242",
            }
        )
        bdio = self.env["business.document.import"]
        partner_dict = {
            "name": "Alexis Delattre",
            "email": "alexis.delattre@example.com",
            "ref": "C1242",
        }
        chatter_msg = []
        domain = []
        order = ""
        partner = bdio._match_partner_ref(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner1)

    def test_match_partner_contact(self):
        partner_email = self.env["res.partner"].create(
            {
                "email": "alexis.email@example.com",
                "name": "Alexis email",
            }
        )
        partner_contact = self.env["res.partner"].create(
            {
                "email": "alexis.name@example.com",
                "name": "Alexis name",
            }
        )
        partner_phone = self.env["res.partner"].create(
            {
                "email": "alexis.phone@example.com",
                "phone": "01.41.98.12.42",
                "name": "Alexis phone",
            }
        )
        bdio = self.env["business.document.import"]
        chatter_msg = []
        domain = []
        order = ""

        partner_dict = {
            "name": "Alexis email",
            "email": "alexis.email@example.com",
        }
        partner = bdio._match_partner_contact(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner_email)

        partner_dict = {
            "contact": "Alexis name",
            "email": "alexis.name@example.com",
        }
        partner = bdio._match_partner_contact(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner_contact)

        partner_dict = {
            "name": "Alexis phone",
            "email": "alexis.phone@example.com",
            "phone": "01.41.98.12.42",
        }
        partner = bdio._match_partner_contact(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner_phone)

    def test_match_partner_name(self):
        partner_name = self.env["res.partner"].create(
            {
                "email": "alexis.name@example.com",
                "name": "Alexis name",
            }
        )
        bdio = self.env["business.document.import"]
        chatter_msg = []
        domain = []
        order = ""

        partner_dict = {
            "name": "Alexis name",
            "email": "alexis.name@example.com",
        }
        partner = bdio._match_partner_name(partner_dict, chatter_msg, domain, order)
        self.assertEqual(partner, partner_name)

    def test_get_partner_website_domain(self):
        bdio = self.env["business.document.import"]

        www_website = {"website": "www.example.com"}
        website_domain = bdio._get_partner_website_domain(www_website)
        self.assertEqual(website_domain, "example.com")

        no_website = bdio._get_partner_website_domain({})
        self.assertEqual(False, no_website)

        https_www_website = {"website": "https://www.example.com"}
        website_domain = bdio._get_partner_website_domain(https_www_website)
        self.assertEqual(website_domain, "example.com")

        https_website = {"website": "https://example.com"}
        website_domain = bdio._get_partner_website_domain(https_website)
        self.assertEqual(website_domain, "example.com")

        https_path_website = {"website": "https://subdomain.example.com/bla/bla"}
        website_domain = bdio._get_partner_website_domain(https_path_website)
        self.assertEqual(website_domain, "example.com")

        https_big_subdomain_website = {
            "website": "https://just.a.big.subdomain.example.com"
        }
        website_domain = bdio._get_partner_website_domain(https_big_subdomain_website)
        self.assertEqual(website_domain, "example.com")

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

        no_error = bdio._match_shipping_partner(
            shipping_dict, None, [], raise_exception=False
        )
        self.assertEqual(no_error, None)

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
        currency_dict = {"xmlid": "base.USD"}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, self.env.ref("base.USD"))
        first_cur = self.env["res.currency"].search([], limit=1)
        currency_dict = {"id": first_cur.id}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, first_cur)
        currency_dict = {"recordset": first_cur}
        res = bdio._match_currency(currency_dict, [])
        self.assertEqual(res, first_cur)
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
        company = self.env["res.company"].browse(1)
        currency_dict = {}
        res = bdio._match_currency(currency_dict, [], company=company)
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
                            "partner_id": self.env.ref("base.res_partner_2").id,
                            "product_code": "TEST1242",
                        },
                    ),
                ],
                "packaging_ids": [(0, 0, {"name": "Big Pack", "barcode": "BIG-PACK"})],
            }
        )
        # Match by code
        product_dict = {"code": "FURN_7777 "}
        res = bdio._match_product(product_dict, [])
        self.assertEqual(res, self.env.ref("product.product_delivery_01"))
        # Match by barcode
        product_dict = {"barcode": "9782203121102"}
        res = bdio._match_product(product_dict, [])
        self.assertEqual(res, product1)
        # Match by packaging barcode
        product_dict = {"barcode": "BIG-PACK"}
        res = bdio._match_product(product_dict, [])
        self.assertEqual(res, product1)
        # Match by seller
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
            logger.info("Exception catched.")

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
        uom_dict = {"name": "lb"}
        res = bdio._match_uom(uom_dict, [])
        self.assertEqual(res, self.env.ref("uom.product_uom_lb"))
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
                "account_type": "expense",
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
                "account_type": "expense",
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
                "account_type": "expense",
            }
        )
        chatter = []
        res = bdio._match_account({"code": "898999"}, chatter)
        self.assertEqual(acc, res)
        self.assertEqual(len(chatter), 1)

    def _prepare_company(self, vat):
        company = self.env.company
        company.partner_id.write({"country_id": self.env.ref("base.es").id, "vat": vat})
        return company

    def test01_check_company_document_vat_without_prefix(self):
        company = self._prepare_company("ESB12345674")
        chatter_msg = []
        self.env["business.document.import"]._check_company(
            {"vat": "B12345674"}, chatter_msg, company=company
        )
        self.assertEqual(chatter_msg, [])

    def test02_check_company_company_vat_without_prefix(self):
        company = self._prepare_company("B12345674")
        chatter_msg = []
        self.env["business.document.import"]._check_company(
            {"vat": "ESB12345674"}, chatter_msg, company=company
        )
        self.assertEqual(chatter_msg, [])

    def test03_check_company_document_vat_separators_lowercase(self):
        company = self._prepare_company("ESB12345674")
        chatter_msg = []
        self.env["business.document.import"]._check_company(
            {"vat": "es b-12.345.674"}, chatter_msg, company=company
        )
        self.assertEqual(chatter_msg, [])

    def test04_check_company_other_country_prefix_blocks(self):
        company = self._prepare_company("ESB12345674")
        with self.assertRaises(UserError) as error:
            self.env["business.document.import"]._check_company(
                {"vat": "FRB12345674"}, [], company=company
            )
        self.assertIn("FRB12345674", str(error.exception))

    def test05_check_company_different_vat_blocks(self):
        company = self._prepare_company("ESB12345674")
        bdio = self.env["business.document.import"]
        for vat in ("B99999997", "ESB99999997"):
            with self.assertRaises(UserError) as error:
                bdio._check_company({"vat": vat}, [], company=company)
            self.assertIn(vat, str(error.exception))

    def test06_check_company_mismatch_without_raise(self):
        company = self._prepare_company("ESB12345674")
        chatter_msg = []
        self.env["business.document.import"]._check_company(
            {"vat": "B99999997"},
            chatter_msg,
            company=company,
            raise_exception=False,
        )
        self.assertEqual(len(chatter_msg), 1)

    def test07_check_company_vat_empty_after_normalize_blocks(self):
        company = self._prepare_company("ESB12345674")
        with self.assertRaises(UserError) as error:
            self.env["business.document.import"]._check_company(
                {"vat": "ES"}, [], company=company
            )
        self.assertIn("ESB12345674", str(error.exception))

    def test08_normalize_vat_company_without_country(self):
        company = self.env["res.company"].create({"name": "Company without country"})
        self.assertFalse(company.partner_id.country_id)
        bdio = self.env["business.document.import"]
        self.assertEqual(
            bdio._normalize_vat_for_company_check("es b-12.345.674", company),
            "ESB12345674",
        )

    def test09_normalize_vat_greek_company(self):
        company = self.env["res.company"].create(
            {"name": "Greek company", "country_id": self.env.ref("base.gr").id}
        )
        bdio = self.env["business.document.import"]
        self.assertEqual(
            bdio._normalize_vat_for_company_check("EL123456783", company),
            "123456783",
        )
        self.assertEqual(
            bdio._normalize_vat_for_company_check("GR123456783", company),
            "GR123456783",
        )
