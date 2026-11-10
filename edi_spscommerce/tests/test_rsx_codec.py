# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests.common import TransactionCase

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.edi_spscommerce.services import rsx

ORDERS_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<Orders xmlns="http://www.spscommerce.com/RSX">
  <Order>
    <Meta>
      <InterchangeSenderID>TP-SENDER</InterchangeSenderID>
      <IsDropShip>true</IsDropShip>
    </Meta>
    <Header>
      <OrderHeader>
        <TradingPartnerId>TP1</TradingPartnerId>
        <PurchaseOrderNumber>PO-900</PurchaseOrderNumber>
        <TsetPurposeCode>00</TsetPurposeCode>
        <PurchaseOrderDate>2026-11-05</PurchaseOrderDate>
      </OrderHeader>
      <Address>
        <AddressTypeCode>ST</AddressTypeCode>
        <AddressName>Store 1</AddressName>
        <Address1>123 Main St</Address1>
        <City>Springfield</City>
        <State>IL</State>
        <PostalCode>62701</PostalCode>
        <Country>US</Country>
      </Address>
      <Dates>
        <DateTimeQualifier>002</DateTimeQualifier>
        <Date>2026-11-20</Date>
      </Dates>
    </Header>
    <LineItem>
      <OrderLine>
        <LineSequenceNumber>1</LineSequenceNumber>
        <VendorPartNumber>SKU-1</VendorPartNumber>
        <BuyerPartNumber>CUST-1</BuyerPartNumber>
        <OrderQty>10</OrderQty>
        <OrderQtyUOM>EA</OrderQtyUOM>
        <PurchasePrice>12.50</PurchasePrice>
      </OrderLine>
    </LineItem>
    <Summary>
      <TotalAmount>125.00</TotalAmount>
      <TotalLineItemNumber>1</TotalLineItemNumber>
    </Summary>
  </Order>
</Orders>
"""


class TestRsxCodec(TransactionCase):
    """Parser tests for the RSX codec (no DB records needed).

    The codec returns raw schema-shaped dicts — assertions read the same
    element names as the SPS documentation.
    """

    def test_parse_orders_minimal(self):
        orders = rsx.parse_orders(ORDERS_XML)
        self.assertEqual(len(orders), 1)
        order = orders[0]
        header = order["Header"]
        order_header = header["OrderHeader"]
        self.assertEqual(order_header["TradingPartnerId"], "TP1")
        self.assertEqual(order_header["PurchaseOrderNumber"], "PO-900")
        self.assertEqual(order_header["TsetPurposeCode"], "00")
        self.assertEqual(order_header["PurchaseOrderDate"], "2026-11-05")
        self.assertEqual(order["Meta"]["IsDropShip"], "true")
        self.assertEqual(order["Meta"]["InterchangeSenderID"], "TP-SENDER")
        # FORCE_LIST keeps single-child groups as lists
        self.assertEqual(header["Address"][0]["AddressTypeCode"], "ST")
        self.assertEqual(header["Address"][0]["City"], "Springfield")
        self.assertEqual(header["Dates"][0]["DateTimeQualifier"], "002")
        self.assertEqual(len(order["LineItem"]), 1)
        line = order["LineItem"][0]["OrderLine"]
        self.assertEqual(line["LineSequenceNumber"], "1")
        self.assertEqual(line["OrderQty"], "10")
        self.assertEqual(line["OrderQtyUOM"], "EA")
        self.assertEqual(line["PurchasePrice"], "12.50")
        self.assertEqual(line["VendorPartNumber"], "SKU-1")
        self.assertEqual(line["BuyerPartNumber"], "CUST-1")
        self.assertEqual(order["Summary"]["TotalAmount"], "125.00")
        self.assertEqual(order["Summary"]["TotalLineItemNumber"], "1")

    def test_parse_orders_rejects_wrong_root(self):
        with self.assertRaises(ValueError):
            rsx.parse_orders(b"<Shipments xmlns='http://www.spscommerce.com/RSX'/>")

    def test_root_document(self):
        data = rsx.parse(ORDERS_XML)
        self.assertEqual(rsx.root_document(data), "orders")


class TestRsxTemplates(AccountTestInvoicingCommon):
    """Render tests for the outbound QWeb templates.

    The templates consume the business record directly (``record``), so
    these tests build real orders/pickings/invoices — the user-facing
    surface is the XML that goes on the wire. Outputs are parsed back
    with the same codec, so the tests double as round-trip checks.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The test user needs the sales group to create sale orders.
        cls.env.user.group_ids += cls.env.ref("sales_team.group_sale_salesman")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Store 1",
                "ref": "TP1",
                "street": "123 Main St",
                "city": "Springfield",
                "zip": "62701",
                "country_id": cls.env.ref("base.us").id,
                "state_id": cls.env.ref("base.state_us_13").id,  # Illinois
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "default_code": "SKU-1",
                "barcode": "1234567890123",
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "client_order_ref": "PO-900",
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "price_unit": 12.5,
                        }
                    )
                ],
            }
        )
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids

    def _render(self, xmlid, values):
        view = self.env.ref(xmlid)
        return view._render_template(view.id, values)

    def test_shipments_template_renders_picking(self):
        output = self._render(
            "edi_spscommerce.qweb_sps_shipments",
            {
                "record": self.picking,
                "meta": {"sender_unique_id": "US", "receiver_unique_id": "TP1"},
            },
        )
        data = rsx.parse(output)
        self.assertEqual(rsx.root_document(data), "shipments")
        shipment = data["Shipments"]["Shipment"][0]
        header = shipment["Header"]
        self.assertEqual(
            header["ShipmentHeader"]["ShipmentIdentification"],
            self.picking.name,
        )
        self.assertEqual(header["ShipmentHeader"]["TradingPartnerId"], "TP1")
        self.assertEqual(header["Address"][0]["AddressTypeCode"], "ST")
        self.assertEqual(header["Address"][0]["City"], "Springfield")
        order_level = shipment["OrderLevel"][0]
        self.assertEqual(order_level["OrderHeader"]["PurchaseOrderNumber"], "PO-900")
        line = order_level["ItemLevel"][0]["ShipmentLine"]
        self.assertEqual(line["VendorPartNumber"], "SKU-1")
        self.assertEqual(line["GTIN"], "1234567890123")
        self.assertEqual(line["ShipQty"], "10.0")

    def test_invoices_template_renders_move(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": "2026-11-10",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 10,
                            "price_unit": 12.5,
                        }
                    )
                ],
            }
        )
        # Keep the total deterministic: the test DB may add default taxes.
        move.invoice_line_ids.tax_ids = [Command.clear()]
        output = self._render(
            "edi_spscommerce.qweb_sps_invoices",
            {
                "record": move,
                "meta": {"sender_unique_id": "US", "receiver_unique_id": "TP1"},
            },
        )
        data = rsx.parse(output)
        self.assertEqual(rsx.root_document(data), "invoices")
        invoice = data["Invoices"]["Invoice"][0]
        header = invoice["Header"]
        self.assertEqual(header["InvoiceHeader"]["InvoiceDate"], "2026-11-10")
        self.assertEqual(header["InvoiceHeader"]["InvoiceTypeCode"], "DI")
        self.assertEqual(header["Address"][0]["AddressTypeCode"], "BT")
        self.assertEqual(header["Address"][0]["City"], "Springfield")
        line = invoice["LineItem"][0]["InvoiceLine"]
        self.assertEqual(line["VendorPartNumber"], "SKU-1")
        self.assertEqual(line["InvoiceQty"], "10.0")
        self.assertEqual(line["PurchasePrice"], "12.5")
        self.assertEqual(invoice["Summary"]["TotalAmount"], "125.0")


class TestSpsBackendConfig(TransactionCase):
    def test_test_mode_resolves_test_dirs(self):
        """The shipped SPS backend reads testout/testin in test mode."""
        backend = self.env.ref("edi_spscommerce.edi_backend_sps")
        self.assertTrue(backend.test_mode_supported)
        backend.test_mode = True
        self.assertEqual(backend.get_conn_parameter("input_dir_pending"), "testout")
        self.assertEqual(backend.get_conn_parameter("output_dir_pending"), "testin")
        backend.test_mode = False
        self.assertEqual(backend.get_conn_parameter("input_dir_pending"), "out")
        self.assertEqual(backend.get_conn_parameter("output_dir_pending"), "in")
