# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import Component

from .common import EDIBackendCommonComponentRegistryTestCase


class EDIBackendTestMatchCase(EDIBackendCommonComponentRegistryTestCase):
    def test_component_match(self):
        """Lookup with special match method."""

        class MatchByBackendTypeOnly(Component):
            _name = "backend_type.only"
            _inherit = "edi.component.mixin"
            _usage = "generate"
            _backend_type = "demo_backend"
            _apply_on = ["res.partner"]

        class MatchByExchangeTypeOnly(Component):
            _name = "exchange_type.only"
            _inherit = "edi.component.mixin"
            _usage = "generate"
            _exchange_type = "test_csv_output"
            _apply_on = ["res.partner"]

        class MatchByBackendExchangeType(Component):
            _name = "backend_type.and.exchange_type"
            _inherit = "edi.component.mixin"
            _usage = "generate"
            _backend_type = "demo_backend"
            _exchange_type = "test_csv_output"
            _apply_on = ["res.partner"]

        self._build_components(
            MatchByBackendTypeOnly,
            MatchByExchangeTypeOnly,
            # This one is registered last but since edi.backend
            # is going to sort them by priority, we'll get the right one
            # when looking for both match
            MatchByBackendExchangeType,
        )

        # Record not relevant for these tests
        work_ctx = {"exchange_record": self.env["edi.exchange.record"].browse()}

        # Search by both backend and exchange type
        component = self.backend._find_component(
            "res.partner",
            ["generate"],
            work_ctx=work_ctx,
            backend_type="demo_backend",
            exchange_type="test_csv_output",
        )
        self.assertEqual(component._name, MatchByBackendExchangeType._name)

        # Search by backend type only
        component = self.backend._find_component(
            "res.partner", ["generate"], work_ctx=work_ctx, backend_type="demo_backend"
        )
        self.assertEqual(component._name, MatchByBackendTypeOnly._name)

        # Search by exchange type only
        component = self.backend._find_component(
            "res.partner",
            ["generate"],
            work_ctx=work_ctx,
            exchange_type="test_csv_output",
        )
        self.assertEqual(component._name, MatchByExchangeTypeOnly._name)
