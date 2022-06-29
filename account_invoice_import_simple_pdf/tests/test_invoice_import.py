# Copyright 2021 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_compare


class TestInvoiceImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "country_id": self.env.ref("base.fr").id,
                "simple_pdf_date_format": "dd-mm-y4",
                "simple_pdf_date_separator": "slash",
            }
        )
        aiispfo = self.env["account.invoice.import.simple.pdf.fields"]
        self.date_field = aiispfo.create(
            {
                "name": "date",
                "extract_rule": "first",
                "partner_id": self.partner.id,
            }
        )
        self.amount_field = aiispfo.create(
            {
                "name": "amount_total",
                "extract_rule": "first",
                "partner_id": self.partner.id,
            }
        )
        self.inv_num_field = aiispfo.create(
            {
                "name": "invoice_number",
                "extract_rule": "first",
                "partner_id": self.partner.id,
            }
        )

        self.partner_config = self.partner._simple_pdf_partner_config()
        self.test_info = {"test_mode": True}
        self.env["account.invoice.import"]._simple_pdf_update_test_info(self.test_info)
        aiispfo = self.env["account.invoice.import.simple.pdf.fields"]
        self.space_chars = list(self.test_info["space_pattern"][1:-1])
        frtax = self.env["account.tax"].create(
            {
                "name": "French VAT purchase 20.0%",
                "description": "FR-VAT-buy-20.0",
                "amount": 20,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        self.module = "account_invoice_import_simple_pdf"
        self.product = self.env.ref("%s.mobile_phone" % self.module)
        self.product.supplier_taxes_id = [(6, 0, [frtax.id])]
        self.demo_partner = self.env.ref("%s.bouygues_telecom" % self.module)
        self.filename = "bouygues_telecom-test.pdf"
        with file_open("%s/tests/pdf/%s" % (self.module, self.filename), "rb") as f:
            self.pdf_file = f.read()
            self.pdf_file_b64 = base64.b64encode(self.pdf_file)

    def test_date_parsing(self):
        date_test = {
            "14/07/2021": {
                "date_format": "dd-mm-y4",
                "date_separator": "slash",
                "lang": "any",
            },
            "14/7/2021": {
                "date_format": "dd-mm-y4",
                "date_separator": "slash",
                "lang": "any",
            },
            "14-7-2021": {
                "date_format": "dd-mm-y4",
                "date_separator": "dash",
                "lang": "any",
            },
            "7/14/2021": {
                "date_format": "mm-dd-y4",
                "date_separator": "slash",
                "lang": "any",
            },
            "7.14.2021": {
                "date_format": "mm-dd-y4",
                "date_separator": "dot",
                "lang": "any",
            },
            "14%sJuillet%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "14%s Juillet%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },  # with double space
            "14%sJuillet,%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "14%sjuillet%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "14%sjuillet,%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "14%sjuil.%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "14%sjuil.,%s2021": {
                "date_format": "dd-month-y4",
                "date_separator": "space",
                "lang": "fr",
            },
            "july%s14%s2021": {
                "date_format": "month-dd-y4",
                "date_separator": "space",
                "lang": "en",
            },
            "july%s14,%s2021": {
                "date_format": "month-dd-y4",
                "date_separator": "space",
                "lang": "en",
            },
            "jul.%s14,%s2021": {
                "date_format": "month-dd-y4",
                "date_separator": "space",
                "lang": "en",
            },
            "july%s14th,%s2021": {
                "date_format": "month-dd-y4",
                "date_separator": "space",
                "lang": "en",
            },
        }
        for src, config in date_test.items():
            raw_text = "Debit 15.12\n%s\n12.99 Total" % src
            if config["date_separator"] == "space":
                raw_text_list = [
                    raw_text % (space_char, space_char)
                    for space_char in self.space_chars
                ]
            else:
                raw_text_list = [raw_text]
            parsed_inv = {"failed_fields": []}
            self.date_field.write(
                {
                    "date_format": config["date_format"],
                    "date_separator": config["date_separator"],
                }
            )
            lang_list = config["lang"] == "any" and ["fr", "en"] or [config["lang"]]
            for lang in lang_list:
                self.partner_config["lang_short"] = lang
                for raw_txt in raw_text_list:
                    self.date_field._get_date(
                        parsed_inv, raw_txt, self.partner_config, self.test_info
                    )
                    res_date = parsed_inv["date"]
                    self.assertEqual(fields.Date.to_string(res_date), "2021-07-14")

    def test_date_parsing_with_accents(self):
        testdict = {
            "20 février 2021": "2021-02-20",
            "25 décembre 2021": "2021-12-25",
            "15 août 2021": "2021-08-15",
            "25 décembre 2021": "2021-12-25",  # use combining acute accent \u0301
            "15 août 2021": "2021-08-15",  # use combining circumflex accent \u0302
            "1er février 2022": "2022-02-01",
        }
        self.date_field.write(
            {
                "date_format": "dd-month-y4",
                "date_separator": "space",
            }
        )
        self.partner_config["lang_short"] = "fr"
        for src_string, result in testdict.items():
            raw_text = "Débit 15,12\n%s\nTotal TTC 12,99" % src_string
            parsed_inv = {"failed_fields": []}
            self.date_field._get_date(
                parsed_inv, raw_text, self.partner_config, self.test_info
            )
            self.assertEqual(fields.Date.to_string(parsed_inv["date"]), result)

    def test_restrict_text(self):
        cut_test = {
            "T1 ici et là POUET là et par là POUET": {
                "start": "POUET",
                "end": "POUET",
                "res": " là et par là ",
            },
            "T2 ici et là POUET là et par là POUET": {
                "start": "POUET",
                "res": " là et par là POUET",
            },
            "T3 ici et là POUET là et par là POUET": {
                "end": "POUET",
                "res": "T3 ici et là ",
            },
        }
        # I use the date field, but I could use any other field
        self.test_info[self.date_field.name] = {}
        for raw_txt, config in cut_test.items():
            self.date_field.write(
                {
                    "start": config.get("start"),
                    "end": config.get("end"),
                }
            )
            res = self.date_field.restrict_text(raw_txt, self.test_info)
            self.assertEqual(res, config["res"])

    def test_amount_parsing(self):
        amount_test = {
            "$ 1.02": {
                "decimal_separator": "dot",
                "thousand_separator": "comma",
                "result": 1.02,
                "currency": "USD",
            },
            "$ 459.09": {
                "decimal_separator": "dot",
                "thousand_separator": "comma",
                "result": 459.09,
                "currency": "USD",
            },
            "$ 1,459.32": {
                "decimal_separator": "dot",
                "thousand_separator": "comma",
                "result": 1459.32,
                "currency": "USD",
            },
            "1.459,32 €": {
                "decimal_separator": "comma",
                "thousand_separator": "dot",
                "result": 1459.32,
                "currency": "EUR",
            },
            "59,32 €": {
                "decimal_separator": "comma",
                "thousand_separator": "space",
                "result": 59.32,
                "currency": "EUR",
            },
            "781.459,32 €": {
                "decimal_separator": "comma",
                "thousand_separator": "dot",
                "result": 781459.32,
                "currency": "EUR",
            },
            "781%s459,32€": {
                "decimal_separator": "comma",
                "thousand_separator": "space",
                "result": 781459.32,
                "currency": "EUR",
            },
            "99459,32 €": {
                "decimal_separator": "comma",
                "thousand_separator": "none",
                "result": 99459.32,
                "currency": "EUR",
            },
            "42'888.99 CHF": {
                "decimal_separator": "dot",
                "thousand_separator": "apostrophe",
                "result": 42888.99,
                "currency": "CHF",
            },
            "14%s459 XPF": {
                "decimal_separator": "comma",
                "thousand_separator": "space",
                "result": 14459,
                "currency": "XPF",
            },  # XPF decimal places = 0
            "14%s459,123 XPF": {
                "decimal_separator": "comma",
                "thousand_separator": "space",
                "result": 14459.123,
                "currency": "TND",
            },  # TND decimal places = 3
            "88,459.1234 VEF": {
                "decimal_separator": "dot",
                "thousand_separator": "comma",
                "result": 88459.1234,
                "currency": "VEF",
            },  # VEF decimal places = 4
        }
        for src, config in amount_test.items():
            raw_text = (
                "Invoice Date: 05/12/2019\n%s\nSAS with a capital of 1,234,322.23 USD"
                % src
            )
            if config["thousand_separator"] == "space" and "%s" in raw_text:
                raw_text_list = [
                    raw_text % space_char for space_char in self.space_chars
                ]
            else:
                raw_text_list = [raw_text]
            parsed_inv = {"failed_fields": []}
            self.partner.write(
                {
                    "simple_pdf_decimal_separator": config["decimal_separator"],
                    "simple_pdf_thousand_separator": config["thousand_separator"],
                    "simple_pdf_currency_id": self.env.ref(
                        "base.%s" % config["currency"]
                    ).id,
                }
            )
            partner_config = self.partner._simple_pdf_partner_config()
            if partner_config["currency"].decimal_places == 0:
                self.amount_field.write({"extract_rule": "last"})
            else:
                self.amount_field.write({"extract_rule": "first"})
            for raw_txt in raw_text_list:
                self.amount_field._get_amount_total(
                    parsed_inv, raw_txt, partner_config, self.test_info
                )
                res_amount = parsed_inv["amount_total"]
                self.assertFalse(
                    partner_config["currency"].compare_amounts(
                        res_amount, config["result"]
                    )
                )

    def test_invoice_number_parsing(self):
        inv_num_test = {
            "INV/2020/05/0042": [
                {"string_type": "fixed", "fixed_char": "INV/"},
                {"string_type": "year4"},
                {"string_type": "fixed", "fixed_char": "/"},
                {"string_type": "month"},
                {"string_type": "fixed", "fixed_char": "/"},
                {"string_type": "digit", "occurrence_min": 4, "occurrence_max": 5},
            ],
            "I210042": [
                {"string_type": "fixed", "fixed_char": "I"},
                {"string_type": "year2"},
                {"string_type": "digit", "occurrence_min": 4, "occurrence_max": 5},
            ],
            "INV2107ZB0042": [
                {"string_type": "fixed", "fixed_char": "INV"},
                {"string_type": "year2"},
                {"string_type": "month"},
                {
                    "string_type": "letter_upper",
                    "occurrence_min": 2,
                    "occurrence_max": 2,
                },
                {"string_type": "digit", "occurrence_min": 4, "occurrence_max": 5},
            ],
            # If you wonder which company can have such a stupid invoice number,
            # the answer is... Orange ! I won't say what I think about these guys...
            "04B700L456 21A7- 1J01": [
                {"string_type": "fixed", "fixed_char": "04B700L456"},
                {"string_type": "space"},
                {"string_type": "year2"},
                {
                    "string_type": "letter_upper",
                    "occurrence_min": 1,
                    "occurrence_max": 1,
                },
                {"string_type": "digit", "occurrence_min": 1, "occurrence_max": 1},
                {"string_type": "fixed", "fixed_char": "-"},
                {"string_type": "space"},
                {"string_type": "fixed", "fixed_char": "1J"},
                {"string_type": "month"},
            ],
        }
        for src, config_list in inv_num_test.items():
            raw_txt = "Invoice number: %s dated 20/08/2020" % src
            self.partner.simple_pdf_invoice_number_ids.unlink()
            self.partner.write(
                {"simple_pdf_invoice_number_ids": [(0, 0, x) for x in config_list]}
            )
            parsed_inv = {"failed_fields": []}
            self.inv_num_field._get_invoice_number(
                parsed_inv, raw_txt, self.partner_config, self.test_info
            )
            self.assertEqual(src, parsed_inv["invoice_number"])

    def test_raw_extraction(self):
        aiio = self.env["account.invoice.import"]
        res = aiio.simple_pdf_text_extraction(self.pdf_file, self.test_info)
        self.assertIsInstance(res, dict)
        self.assertTrue(len(res["all"]) >= len(res["first"]))
        self.assertIn("FR 74 397 480 930", res["first"])
        self.assertIn("FR74397480930", res["first_no_space"])

    def test_complete_import(self):
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": self.pdf_file_b64,
                "invoice_filename": self.filename,
            }
        )
        wiz.import_invoice()
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.demo_partner.id),
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "11608848301659"),
            ]
        )
        inv_config = self.env.ref("%s.bouygues_telecom_import_config" % self.module)
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2019-11-02")
        self.assertEqual(inv.journal_id.type, "purchase")
        self.assertEqual(inv.currency_id, self.env.ref("base.EUR"))
        self.assertFalse(inv.currency_id.compare_amounts(inv.amount_total, 12.99))
        self.assertFalse(inv.currency_id.compare_amounts(inv.amount_untaxed, 10.83))
        self.assertEqual(len(inv.invoice_line_ids), 1)
        iline = inv.invoice_line_ids[0]
        self.assertEqual(iline.name, inv_config.label)
        self.assertEqual(iline.product_id, self.product)
        self.assertEqual(iline.tax_ids, self.product.supplier_taxes_id)
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=2), 0)
        self.assertEqual(float_compare(iline.price_unit, 10.83, precision_digits=2), 0)
        inv.unlink()

    def test_complete_import_pdfplumber(self):
        icpo = self.env["ir.config_parameter"]
        key = "invoice_import_simple_pdf.pdf2txt"
        method = "pdfplumber"
        configp = icpo.search([("key", "=", key)])
        if configp:
            configp.write({"value": method})
        else:
            icpo.create({"key": key, "value": method})
        self.test_complete_import()

    def test_test_mode(self):
        self.demo_partner.write(
            {
                "simple_pdf_test_file": self.pdf_file_b64,
                "simple_pdf_test_filename": self.filename,
            }
        )
        self.demo_partner.pdf_simple_test_run()
        self.assertTrue(self.demo_partner.simple_pdf_test_results)
        self.assertTrue(self.demo_partner.simple_pdf_test_raw_text)
        self.demo_partner.pdf_simple_test_cleanup()
        self.assertFalse(self.demo_partner.simple_pdf_test_results)
        self.assertFalse(self.demo_partner.simple_pdf_test_raw_text)
        self.assertFalse(self.demo_partner.simple_pdf_test_file)
