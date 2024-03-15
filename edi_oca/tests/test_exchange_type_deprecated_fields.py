# Copyright 2023 Camptocamp SA (https://www.camptocamp.com).
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from .common import EDIBackendCommonTestCase


class EDIExchangeTypeDeprecatedFieldsTestCase(EDIBackendCommonTestCase):
    def test_inverse(self):
        typ = self.exchange_type_out
        self.assertFalse(typ.rule_ids)
        self.assertFalse(typ.deprecated_rule_fields_still_used)
        typ.model_ids += self.env["ir.model"]._get("res.partner")
        self.assertTrue(typ.deprecated_rule_fields_still_used)
        self.assertEqual(typ.rule_ids.mapped("model_id.model"), ["res.partner"])
        typ.model_ids += self.env["ir.model"]._get("res.groups")
        self.assertEqual(
            typ.rule_ids.mapped("model_id.model"), ["res.partner", "res.groups"]
        )
        typ.enable_domain = "[(1, '=', 1)]"
        self.assertRecordValues(
            typ.rule_ids, [{"enable_domain": typ.enable_domain, "kind": "custom"}] * 2
        )
        typ.model_manual_btn = True
        self.assertRecordValues(
            typ.rule_ids, [{"enable_domain": typ.enable_domain, "kind": "form_btn"}] * 2
        )
        typ.model_ids -= self.env["ir.model"]._get("res.groups")
        self.assertEqual(typ.rule_ids.mapped("model_id.model"), ["res.partner"])
        typ.model_ids = False
        self.assertFalse(typ.rule_ids)

    def test_btn(self):
        typ = self.exchange_type_out
        typ.model_ids += self.env["ir.model"]._get("res.partner")
        typ.enable_domain = "[(1, '=', 1)]"
        typ.button_wipe_deprecated_rule_fields()
        self.assertFalse(typ.model_ids)
        self.assertFalse(typ.enable_domain)
        self.assertFalse(typ.enable_snippet)
        # Rules are kept
        self.assertEqual(typ.rule_ids.mapped("model_id.model"), ["res.partner"])
