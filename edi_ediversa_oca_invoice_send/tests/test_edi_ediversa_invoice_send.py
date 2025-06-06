# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import base64
import io
from unittest.mock import patch

from odoo import fields

from odoo.addons.edi_ediversa_oca.components.ediversa_api import EdiversaApi
from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class TestEdiEdiversaInvoiceSend(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.env.company.write(
            {
                "use_edi_ediversa": True,
                "edi_ediversa_test": True,
                "edi_ediversa_user": "test",
                "edi_ediversa_password": "test",
                "vat": "ES11223344X",
            }
        )
        cls.env.company.partner_id.write({"ediversa_id": "1000000000"})
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test-Customer",
                "ediversa_id": "0000000001",
                "child_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test-Customer Invoice",
                            "type": "invoice",
                            "ediversa_id": "0000000002",
                            "ediversa_send_invoice": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test-Customer Shipping",
                            "type": "delivery",
                            "ediversa_id": "0000000003",
                        },
                    ),
                ],
            }
        )
        cls.account_tax = cls.env["account.tax"].create(
            {
                "name": "Tax 10%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 10.0,
                "company_id": cls.env.company.id,
                "ediversa_tax_type": "VAT",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "barcode": "11111111",
                "invoice_policy": "order",
            }
        )
        uom_kg_id = cls.env.ref("uom.product_uom_kgm").id
        cls.product_kg = cls.env["product.product"].create(
            {
                "name": "Test Product - Kg",
                "barcode": "22222222",
                "invoice_policy": "order",
                "uom_id": uom_kg_id,
            }
        )
        uom_l_id = cls.env.ref("uom.product_uom_litre").id
        cls.product_l = cls.env["product.product"].create(
            {
                "name": "Test Product - L",
                "barcode": "33333333",
                "invoice_policy": "order",
                "uom_id": uom_l_id,
            }
        )
        uom_c_id = cls.env.ref("uom.product_uom_cubic_meter").id
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Test Product - C",
                "barcode": "44444444",
                "invoice_policy": "order",
                "uom_id": uom_c_id,
            }
        )
        uom_t_id = cls.env.ref("uom.product_uom_ton").id
        cls.product_t = cls.env["product.product"].create(
            {
                "name": "Test Product - T",
                "barcode": "55555555",
                "invoice_policy": "order",
                "uom_id": uom_t_id,
            }
        )
        uom_m_id = cls.env.ref("uom.product_uom_meter").id
        cls.product_m = cls.env["product.product"].create(
            {
                "name": "Test Product - M",
                "barcode": "66666666",
                "invoice_policy": "order",
                "uom_id": uom_m_id,
            }
        )
        return res

    def create_sale(self):
        customer = self.customer
        delivery_addres = fields.first(
            customer.child_ids.filtered(lambda a: a.type == "delivery")
        )
        invoice_addres = fields.first(
            customer.child_ids.filtered(lambda a: a.type == "invoice")
        )
        sale = self.env["sale.order"].create(
            {
                "partner_id": customer.id,
                "partner_invoice_id": invoice_addres.id,
                "partner_shipping_id": delivery_addres.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 10,
                            "price_unit": 100,
                            "tax_id": [self.account_tax.id],
                        },
                    ),
                ],
            }
        )
        return sale

    def check_partner_line(self, index, value, invoice):
        partner = False
        if index in ["NADBY", "NADIV"]:
            partner = invoice.partner_id
        elif index in ["NADSU", "NADSCO"]:
            partner = invoice.company_id.partner_id
        elif index in ["NADBCO", "NADPR"]:
            partner = invoice.partner_id.commercial_partner_id
        elif index in ["NADDP"]:
            partner = invoice.partner_shipping_id
        if partner:
            self.assertEqual(value, partner.ediversa_id)

    def check_line(self, line, sale, invoice):
        line = line.decode().rstrip("\n")
        elements = line.split("|")
        index = elements[0]
        if index in ["NADBY", "NADIV", "NADSU", "NADSCO", "NADBCO", "NADPR", "NADDP"]:
            self.check_partner_line(index, elements[1], invoice)
        else:
            if index == "INV":
                self.assertEqual(elements[1], invoice.name)
            elif index == "DTM":
                self.assertEqual(elements[1], invoice.invoice_date.strftime("%Y%m%d"))
            elif index == "CUX":
                self.assertEqual(elements[1], invoice.currency_id.name)
            elif index == "RFF":
                if elements[1] == "ON":
                    self.assertEqual(elements[2], sale.name)
                elif elements[1] == "DQ":
                    self.assertEqual(elements[2], sale.picking_ids[0].name)
            elif index == "LIN":
                self.assertEqual(
                    elements[1], invoice.invoice_line_ids[0].product_id.barcode
                )
            elif index == "QTYLIN":
                self.assertEqual(elements[2], str(invoice.invoice_line_ids[0].quantity))
            elif index == "PRILIN":
                self.assertEqual(
                    elements[2], str(invoice.invoice_line_ids[0].price_unit)
                )
            elif index == "TAXLIN":
                self.assertEqual(elements[1], "VAT")
            elif index == "MOALIN":
                self.assertEqual(
                    elements[1], str(invoice.invoice_line_ids[0].price_subtotal)
                )
            elif index == "MOARES":
                self.assertEqual(
                    elements[1], str(invoice.invoice_line_ids[0].price_subtotal)
                )
                self.assertEqual(
                    elements[4], str(invoice.invoice_line_ids[0].price_total)
                )
            elif index == "TAXRES":
                self.assertEqual(elements[1], "VAT")

    def test_ediversa_invoice_send(self):
        with patch.object(EdiversaApi, "send_document", return_value="reference"):
            sale = self.create_sale()
            sale.action_confirm()
            invoice = sale._create_invoices()
            invoice.action_post()
            self.assertEqual(invoice.exchange_record_count, 1)
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            backend._cron_check_output_exchange_sync()
            exchange_record = self.env["edi.exchange.record"].search(
                [("res_id", "=", invoice.id), ("model", "=", invoice._name)],
            )
            self.assertTrue(exchange_record)
            self.assertTrue(exchange_record.exchange_file)
            self.assertEqual(
                exchange_record.edi_exchange_state, "output_sent_and_processed"
            )
            self.assertFalse(exchange_record.exchange_error)
            with io.BytesIO(base64.b64decode(exchange_record.exchange_file)) as f:
                lines = f.readlines()
                self.assertTrue("INVOIC_D_93A_UN_EAN007\n" in lines[0].decode())
                for line in lines[1:]:
                    self.check_line(line, sale, invoice)

    def test_ediversa_invoice_send_with_error(self):
        with patch.object(EdiversaApi, "send_document", return_value=False):
            sale = self.create_sale()
            sale.action_confirm()
            invoice = sale._create_invoices()
            invoice.action_post()
            self.assertEqual(invoice.exchange_record_count, 1)
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            backend._cron_check_output_exchange_sync()
            exchange_record = self.env["edi.exchange.record"].search(
                [("res_id", "=", invoice.id), ("model", "=", invoice._name)],
            )
            self.assertTrue(exchange_record)
            self.assertEqual(exchange_record.edi_exchange_state, "output_error_on_send")
            self.assertTrue(exchange_record.exchange_error)

    def test_ediversa_invoice_send_multiple_uom(self):
        with patch.object(EdiversaApi, "send_document", return_value="reference"):
            sale = self.create_sale()
            self.env["sale.order.line"].create(
                {
                    "order_id": sale.id,
                    "product_id": self.product_kg.id,
                    "tax_id": [self.account_tax.id],
                }
            )
            self.env["sale.order.line"].create(
                {
                    "order_id": sale.id,
                    "product_id": self.product_l.id,
                    "tax_id": [self.account_tax.id],
                }
            )
            self.env["sale.order.line"].create(
                {
                    "order_id": sale.id,
                    "product_id": self.product_c.id,
                    "tax_id": [self.account_tax.id],
                }
            )
            self.env["sale.order.line"].create(
                {
                    "order_id": sale.id,
                    "product_id": self.product_t.id,
                    "tax_id": [self.account_tax.id],
                }
            )
            self.env["sale.order.line"].create(
                {
                    "order_id": sale.id,
                    "product_id": self.product_m.id,
                    "tax_id": [self.account_tax.id],
                }
            )
            sale.action_confirm()
            invoice = sale._create_invoices()
            invoice.action_post()
            exchange_record = self.env["edi.exchange.record"].search(
                [("res_id", "=", invoice.id), ("model", "=", invoice._name)],
            )
            self.assertTrue(exchange_record)
            self.assertTrue(exchange_record.exchange_file)
            found_uom = []
            with io.BytesIO(base64.b64decode(exchange_record.exchange_file)) as f:
                lines = f.readlines()
                for line in lines:
                    line = line.decode().rstrip("\n")
                    elements = line.split("|")
                    if elements[0] == "QTYLIN":
                        found_uom.append(elements[3])
            self.assertTrue(found_uom)
            for uom in ["PCE", "KGM", "LTR", "MTQ", "TNE", "MTR"]:
                self.assertTrue(uom in found_uom)
