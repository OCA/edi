# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from .common import EDIBackendCommonTestCase


class EDIExchangeTypeTestCase(EDIBackendCommonTestCase):
    def test_ack_for(self):
        self.assertEqual(self.exchange_type_out.ack_type_id, self.exchange_type_out_ack)
        new_type = self.exchange_type_out.copy({"code": "just_a_test"})
        self.assertEqual(new_type.ack_type_id, self.exchange_type_out_ack)
        self.exchange_type_out_ack.refresh()
        self.assertIn(
            self.exchange_type_out.id, self.exchange_type_out_ack.ack_for_type_ids.ids,
        )
        self.assertIn(
            new_type.id, self.exchange_type_out_ack.ack_for_type_ids.ids,
        )

    def test_advanced_settings(self):
        settings = """
        components:
            foo: this
            boo: that
        whatever:
            ok: True
        """
        self.exchange_type_out.advanced_settings_edit = settings
        # fmt:off
        self.assertEqual(self.exchange_type_out.advanced_settings, {
            "components": {
                "foo": "this",
                "boo": "that",
            },
            "whatever": {
                "ok": True,
            }
        })
        # fmt:on
