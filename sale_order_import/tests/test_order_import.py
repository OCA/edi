# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest import mock

from odoo import exceptions
from odoo.tests.common import Form

from .common import TestCommon


class TestOrderImport(TestCommon):
    """Test order create/update."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env["res.partner"].create(
            {
                "is_company": True,
                "name": "Test sale_order_import",
                "email": "test_partner_so_import@ilovetests.com",
            }
        )
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Test product sale_order_import 1",
                "default_code": "TEST_SOIMPORT1",
                "sale_ok": True,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "lst_price": 10.13,
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Test product sale_order_import 2",
                "default_code": "TEST_SOIMPORT2",
                "sale_ok": True,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "lst_price": 10.12,
            }
        )
        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Test product sale_order_import 3",
                "default_code": "TEST_SOIMPORT3",
                "sale_ok": True,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "lst_price": 10.14,
            }
        )
        cls.parsed_order = {
            "partner": {"email": "test_partner_so_import@ilovetests.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "TEST_SOIMPORT1"},
                    "qty": 2,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                }
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }

    def test_order_import(self):
        order = self.wiz_model.create_order(self.parsed_order, "pricelist")
        self.assertEqual(order.client_order_ref, self.parsed_order["order_ref"])
        self.assertEqual(
            order.order_line[0].product_id.default_code,
            self.parsed_order["lines"][0]["product"]["code"],
        )
        self.assertEqual(int(order.order_line[0].product_uom_qty), 2)
        # Now update the order
        parsed_order_up = dict(
            self.parsed_order,
            partner={"email": "test_partner_so_import@ilovetests.com"},
            lines=[
                {
                    "product": {"code": "TEST_SOIMPORT1"},
                    "qty": 3,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                },
                {
                    "product": {"code": "TEST_SOIMPORT2"},
                    "qty": 1,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 1.42,
                },
            ],
        )
        self.wiz_model.update_order_lines(parsed_order_up, order, "pricelist")
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(int(order.order_line[0].product_uom_qty), 3)
        # test raise UserError if not price_unit
        parsed_order_up_no_price_unit = dict(
            self.parsed_order,
            partner={"email": "test_partner_so_import@ilovetests.com"},
            lines=[
                {
                    "product": {"code": "TEST_SOIMPORT3"},
                    "qty": 4,
                    "uom": {"unece_code": "C62"},
                },
            ],
        )
        parsed_order_up_no_price_unit["doc_type"] = "order"
        parsed_order_up_no_price_unit["price_source"] = "order"
        expected_msg = (
            "No price is defined in the file. Please double check "
            "file or select Pricelist as the source for prices."
        )
        with self.assertRaisesRegex(exceptions.UserError, expected_msg):
            self.wiz_model.update_order_lines(
                parsed_order_up_no_price_unit, order, "order"
            )

    def test_order_import_action(self):
        wiz = self.wiz_model.create({"import_type": "xml"})
        action = wiz.create_order_return_action(self.parsed_order, "order.ref")
        order = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(order.state, "draft")

    def test_order_import_confirm(self):
        wiz = self.wiz_model.create({"import_type": "xml", "confirm_order": True})
        action = wiz.create_order_return_action(self.parsed_order, "order.ref")
        order = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(order.state, "sale")

    def test_order_import_default_so_vals(self):
        default = {"client_order_ref": "OVERRIDE"}
        order = self.wiz_model.with_context(
            sale_order_import__default_vals=dict(order=default)
        ).create_order(self.parsed_order, "pricelist")
        self.assertEqual(order.client_order_ref, "OVERRIDE")

    def test_with_order_buttons(self):
        # Prepare test data
        order_file_data = base64.b64encode(
            b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        )
        order_filename = "test_order.xml"
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")
        # Create a new form
        with Form(
            self.wiz_model.with_context(
                default_order_filename=order_filename,
            )
        ) as form:
            with mock_parse_order as mocked:
                # Return 'rfq' for doc_type
                mocked.return_value = "rfq"
                # Set values for the required fields
                form.import_type = "xml"
                form.order_file = order_file_data
                mocked.assert_called()
                # Test the button with the simulated values
                mocked.return_value = self.parsed_order
                action = form.save().import_order_button()
                self.assertEqual(action["xml_id"], "sale.action_quotations")
                self.assertEqual(action["view_mode"], "form,tree,calendar,graph")
                self.assertEqual(action["view_id"], False)
                mocked.assert_called()
                so = self.env["sale.order"].browse(action["res_id"])
                self.assertEqual(so.partner_id, self.partner1)
                self.assertEqual(so.client_order_ref, "TEST1242")
                self.assertEqual(so.order_line.product_id, self.product1)
                self.assertEqual(so.state, "draft")

        # Create another form to update the above sale order
        with Form(
            self.wiz_model.with_context(
                default_order_filename=order_filename,
            )
        ) as form:
            with mock_parse_order as mocked:
                # Return 'rfq' for doc_type
                mocked.return_value = "rfq"
                # Set the required fields
                form.import_type = "xml"
                form.order_file = order_file_data
                parsed_order_up = dict(
                    self.parsed_order,
                    lines=[
                        {
                            "product": {"code": "TEST_SOIMPORT1"},
                            "qty": 3,
                            "uom": {"unece_code": "C62"},
                            "price_unit": 12.42,
                        },
                        {
                            "product": {"code": "TEST_SOIMPORT2"},
                            "qty": 1,
                            "uom": {"unece_code": "C62"},
                            "price_unit": 1.42,
                        },
                    ],
                )
                mocked.return_value = parsed_order_up
                action = form.save().import_order_button()
                form = form.save()
                self.assertEqual(
                    action["xml_id"], "sale_order_import.sale_order_import_action"
                )
                self.assertEqual(form.state, "update")
                self.assertEqual(form.sale_id, so)
                form.update_order_button()

        self.assertEqual(len(so.order_line), 2)
        self.assertEqual(so.order_line[0].product_uom_qty, 3)
