# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestPunchoutCommon


@tagged("post_install", "-at_install")
class TestPunchoutUomMappingResolution(TestPunchoutCommon):
    """Cover the 6-tier resolution in ``_get_uom_by_supplier_code``."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Mapping = cls.env["punchout.uom.mapping"]
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")
        cls.kg = cls.env.ref("uom.product_uom_kgm")
        cls.litre = cls.env.ref("uom.product_uom_litre")
        cls.supplier = cls.env["res.partner"].create({"name": "Test Supplier"})
        cls.other_supplier = cls.env["res.partner"].create({"name": "Other Supplier"})
        cls.backend.partner_id = cls.supplier

    # --- Resolution priority ---------------------------------------------

    def test_backend_mapping_wins_over_supplier_global_and_unece(self):
        self.Mapping.create({"supplier_code": "XYZ", "uom_id": self.unit.id})  # global
        self.Mapping.create(
            {
                "supplier_code": "XYZ",
                "supplier_id": self.supplier.id,
                "uom_id": self.litre.id,
            }
        )
        self.Mapping.create(
            {
                "supplier_code": "XYZ",
                "backend_id": self.backend.id,
                "uom_id": self.dozen.id,
            }
        )
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "XYZ")
        self.assertEqual(uom, self.dozen)

    def test_supplier_mapping_wins_over_global_and_unece(self):
        self.Mapping.create({"supplier_code": "YYY", "uom_id": self.unit.id})  # global
        self.Mapping.create(
            {
                "supplier_code": "YYY",
                "supplier_id": self.supplier.id,
                "uom_id": self.litre.id,
            }
        )
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "YYY")
        self.assertEqual(uom, self.litre)

    def test_global_mapping_wins_over_unece_and_name(self):
        # STUECK is not a UNECE code, so only global/name would match.
        # Global mapping takes priority over name-based fallback.
        global_mapping = self.Mapping.create(
            {"supplier_code": "STUECK-TEST", "uom_id": self.dozen.id}
        )
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "STUECK-TEST")
        self.assertEqual(uom, global_mapping.uom_id)

    def test_unece_code_resolves(self):
        # KGM is UNECE for kilogram; no mapping defined.
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "KGM")
        self.assertEqual(uom, self.kg)

    def test_unece_code_is_case_insensitive(self):
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "kgm")
        self.assertEqual(uom, self.kg)

    def test_name_match_fallback(self):
        # Odoo ships a uom.uom named exactly "Units" — match by name.
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "Units")
        self.assertEqual(uom, self.unit)

    def test_no_match_returns_empty_recordset(self):
        uom = self.Mapping._get_uom_by_supplier_code(
            self.backend, "ZZZ_NOT_A_REAL_CODE"
        )
        self.assertFalse(uom)

    def test_empty_code_returns_empty_recordset(self):
        self.assertFalse(self.Mapping._get_uom_by_supplier_code(self.backend, ""))
        self.assertFalse(self.Mapping._get_uom_by_supplier_code(self.backend, None))

    def test_supplier_scope_ignored_for_other_supplier(self):
        # Mapping belongs to other_supplier — our backend's partner shouldn't see it.
        self.Mapping.create(
            {
                "supplier_code": "AAA",
                "supplier_id": self.other_supplier.id,
                "uom_id": self.litre.id,
            }
        )
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "AAA")
        self.assertFalse(uom)

    def test_explicit_supplier_param_overrides_backend_partner(self):
        self.Mapping.create(
            {
                "supplier_code": "BBB",
                "supplier_id": self.other_supplier.id,
                "uom_id": self.dozen.id,
            }
        )
        uom = self.Mapping._get_uom_by_supplier_code(
            self.backend, "BBB", supplier=self.other_supplier
        )
        self.assertEqual(uom, self.dozen)

    # --- Default data shipped in data/uom_mapping_data.xml ----------------

    def test_global_default_stueck_resolves(self):
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "STUECK")
        self.assertEqual(uom, self.unit)

    def test_global_default_kg_resolves(self):
        uom = self.Mapping._get_uom_by_supplier_code(self.backend, "KG")
        self.assertEqual(uom, self.kg)

    # --- Scope constraints -----------------------------------------------

    def test_duplicate_global_mapping_rejected(self):
        self.Mapping.create({"supplier_code": "DUP", "uom_id": self.unit.id})
        with self.assertRaises(ValidationError):
            self.Mapping.create({"supplier_code": "DUP", "uom_id": self.dozen.id})

    def test_duplicate_backend_mapping_rejected(self):
        self.Mapping.create(
            {
                "supplier_code": "DUP2",
                "backend_id": self.backend.id,
                "uom_id": self.unit.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.Mapping.create(
                {
                    "supplier_code": "DUP2",
                    "backend_id": self.backend.id,
                    "uom_id": self.dozen.id,
                }
            )

    def test_same_code_different_scopes_allowed(self):
        """A global, a supplier-scoped, and a backend-scoped mapping for the
        same code can coexist — they live in separate scopes."""
        self.Mapping.create({"supplier_code": "OK", "uom_id": self.unit.id})
        self.Mapping.create(
            {
                "supplier_code": "OK",
                "supplier_id": self.supplier.id,
                "uom_id": self.litre.id,
            }
        )
        self.Mapping.create(
            {
                "supplier_code": "OK",
                "backend_id": self.backend.id,
                "uom_id": self.dozen.id,
            }
        )

    def test_empty_supplier_code_rejected(self):
        with self.assertRaises(ValidationError):
            self.Mapping.create({"supplier_code": "   ", "uom_id": self.unit.id})
