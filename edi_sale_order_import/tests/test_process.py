# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import textwrap

import mock

from odoo import exceptions

from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin


class TestProcessComponent(SavepointComponentCase, EDIBackendTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls._get_backend()
        cls.exc_type = cls._create_exchange_type(
            name="Test SO import",
            code="test_so_import",
            direction="input",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.identifier}-{type.code}-{dt}",
            backend_id=cls.backend.id,
            advanced_settings_edit=textwrap.dedent(
                """
            components:
                process:
                    usage: input.process.sale.order
            sale_order_import:
                wiz_ctx:
                    random_key: custom
            """
            ),
        )
        cls.record = cls.backend.create_record("test_so_import", {})
        cls.record._set_file_content(b"<fake><order></order></fake>")
        cls.wiz_model = cls.env["sale.order.import"]

    def test_lookup(self):
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._name, "edi.input.sale.order.process")

    def test_wizard_setup(self):
        comp = self.backend._get_component(self.record, "process")
        with mock.patch.object(
            type(self.wiz_model), "order_file_change"
        ) as md_onchange:
            wiz = comp._setup_wizard()
            self.assertEqual(wiz._name, self.wiz_model._name)
            self.assertEqual(wiz.env.context["random_key"], "custom")
            self.assertEqual(
                base64.b64decode(wiz.order_file), b"<fake><order></order></fake>"
            )
            self.assertEqual(wiz.order_filename, self.record.exchange_filename)
            self.assertEqual(wiz.price_source, "pricelist")
            md_onchange.assert_called()

    def test_settings(self):
        self.exc_type.advanced_settings_edit = textwrap.dedent(
            """
            components:
                process:
                    usage: input.process.sale.order
            sale_order_import:
                price_source: order
                confirm_order: true
            """
        )
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._get_default_price_source(), "order")
        self.assertTrue(comp._order_should_be_confirmed())

    def test_existing_order(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env["res.partner"].search([], limit=1).id}
        )
        comp = self.backend._get_component(self.record, "process")
        m1 = mock.patch.object(type(self.wiz_model), "order_file_change")
        m2 = mock.patch.object(type(self.wiz_model), "import_order_button")
        m3 = mock.patch.object(
            type(self.wiz_model),
            "sale_id",
            new_callable=mock.PropertyMock,
        )
        m4 = mock.patch.object(
            type(self.wiz_model),
            "state",
            new_callable=mock.PropertyMock,
        )
        rec_msgs = self.record.message_ids
        # Simulate the wizard detected an existing order state
        with m1 as md_onchange, m2 as md_btn, m3 as md_sale_id, m4 as md_state:
            md_sale_id.return_value = order
            md_state.return_value = "update"
            with self.assertRaisesRegex(
                exceptions.UserError, "Sales order has already been imported before"
            ):
                comp.process()
                md_onchange.assert_called()
                md_btn.assert_called()
        new_msg = self.record.message_ids - rec_msgs
        self.assertIn("Sales order has already been imported before", new_msg.body)
        self.assertIn(
            f"/web#id={order.id}&amp;model=sale.order&amp;view_type=form", new_msg.body
        )

    def test_new_order(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env["res.partner"].search([], limit=1).id}
        )
        comp = self.backend._get_component(self.record, "process")
        mock1 = mock.patch.object(type(self.wiz_model), "order_file_change")
        mock2 = mock.patch.object(type(self.wiz_model), "import_order_button")
        self.assertFalse(self.record.record)
        # Simulate the wizard detected an existing order state
        with mock1 as md_onchange, mock2 as md_btn:
            md_btn.return_value = {"res_id": order.id}
            res = comp.process()
            md_onchange.assert_called()
            md_btn.assert_called()
            self.assertEqual(res, f"Sales order {order.name} created")

        self.assertEqual(self.record.record, order)
