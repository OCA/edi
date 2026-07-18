# Copyright 2025-2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Tests for the DB-stored invoice2data templates module.

Focus on the data-model contract rather than running invoice2data against
real PDFs (which would need poppler/tesseract on the test runner):

* JSON authoring round-trips through ``ordered_load``.
* Structured authoring (keywords + field_ids) composes a sane template dict.
* The wizard extension merges DB templates into its template list.
"""

import json
from unittest import mock

from odoo.tests.common import TransactionCase


class TestInvoice2dataDBTemplates(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Template = cls.env["invoice2data.template"]
        cls.Field = cls.env["invoice2data.template.field"]

    # === JSON authoring path ===

    def test_get_templates_loads_json_blob(self):
        record = self.Template.create(
            {
                "name": "acme.test.json",
                "keywords": "ACME",
                "template": json.dumps(
                    [
                        {
                            "issuer": "ACME",
                            "keywords": ["ACME"],
                            "exclude_keywords": [],
                            "fields": {
                                "invoice_number": r"Inv\s*#\s*(\d+)",
                                "amount": r"Total\s+([\d.]+)",
                            },
                        }
                    ]
                ),
            }
        )
        templates = record._to_invoice_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].get("template_name"), "acme.test.json")
        self.assertEqual(templates[0]["issuer"], "ACME")

    def test_invalid_json_does_not_raise(self):
        record = self.Template.create(
            {
                "name": "acme.test.broken",
                "keywords": "ACME",
                "template": "this is not json",
            }
        )
        # Must swallow parse errors -- the lib must never crash an import
        # because one DB template is malformed.
        self.assertEqual(record._to_invoice_templates(), [])

    # === Structured authoring path ===

    def test_compose_template_dict_from_fields(self):
        record = self.Template.create(
            {
                "name": "acme.test.fields",
                "keywords": "ACME\nVendor",
                "exclude_keywords": "DRAFT",
                "field_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "invoice_number",
                            "parser": "regex",
                            "regex": r"Inv\s*#\s*(\d+)",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "amount",
                            "parser": "regex",
                            "regex": r"Total\s+([\d.]+)",
                            "type": "float",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "vat",
                            "parser": "static",
                            "static_value": "FR12345678901",
                        },
                    ),
                ],
            }
        )
        composed = record._compose_template_dict()
        self.assertEqual(composed["keywords"], ["ACME", "Vendor"])
        self.assertEqual(composed["exclude_keywords"], ["DRAFT"])
        self.assertEqual(
            composed["fields"]["invoice_number"],
            {"parser": "regex", "regex": r"Inv\s*#\s*(\d+)"},
        )
        self.assertEqual(composed["fields"]["amount"]["type"], "float")
        self.assertEqual(
            composed["fields"]["vat"],
            {"parser": "static", "value": "FR12345678901"},
        )

    def test_field_with_replace_emits_pair(self):
        record = self.Template.create(
            {
                "name": "acme.test.replace",
                "keywords": "ACME",
                "field_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "vat",
                            "parser": "regex",
                            "regex": r"VAT\s+(\S+)",
                            "replace_pattern": r"\W+",
                            "replace_repl": "",
                        },
                    ),
                ],
            }
        )
        composed = record._compose_template_dict()
        self.assertEqual(composed["fields"]["vat"]["replace"], [r"\W+", ""])

    def test_extract_number_only_when_int_or_float(self):
        record = self.Template.create(
            {
                "name": "acme.test.extract_number",
                "keywords": "ACME",
                "field_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "amount",
                            "parser": "regex",
                            "regex": r"qty\s+(\d+\s+Stk\.)",
                            "type": "int",
                            "extract_number": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "vat",
                            "parser": "regex",
                            "regex": r"VAT\s+(\S+)",
                            "type": "char",
                            # extract_number on a Text field: silently ignored,
                            # not surfaced as a bogus template key.
                            "extract_number": True,
                        },
                    ),
                ],
            }
        )
        composed = record._compose_template_dict()
        self.assertTrue(composed["fields"]["amount"]["extract_number"])
        self.assertNotIn("extract_number", composed["fields"]["vat"])

    # === Filtering by template_type ===

    def test_get_templates_filters_by_type_and_active(self):
        active = self.Template.create(
            {
                "name": "acme.purchase.active",
                "keywords": "ACME",
                "template_type": "purchase_invoice",
            }
        )
        self.Template.create(
            {
                "name": "acme.purchase.inactive",
                "keywords": "ACME",
                "template_type": "purchase_invoice",
                "active": False,
            }
        )
        names = [
            tpl["template_name"]
            for tpl in self.Template.get_templates("purchase_invoice")
        ]
        self.assertIn(active.name, names)
        self.assertNotIn("acme.purchase.inactive", names)

    # === Wizard merge ===

    def test_wizard_collect_includes_db_templates(self):
        self.Template.create(
            {
                "name": "acme.purchase.wizardtest",
                "keywords": "ACME",
                "template_type": "purchase_invoice",
            }
        )
        Wizard = self.env["account.invoice.import"]
        with mock.patch(
            "odoo.addons.account_invoice_import_invoice2data_db_templates"
            ".wizard.account_invoice_import.read_templates",
            return_value=[],
        ):
            collected = Wizard._invoice2data_collect_templates()
        names = [
            tpl["template_name"] for tpl in collected if "template_name" in tpl
        ]
        self.assertIn("acme.purchase.wizardtest", names)
