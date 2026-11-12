# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import copy
import os
import tempfile

from odoo import Command, fields
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

    def test_xsd_validate(self):
        """Payloads validate against a user-supplied XSD when enabled."""
        xsd = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns="http://www.spscommerce.com/RSX"
    targetNamespace="http://www.spscommerce.com/RSX"
    elementFormDefault="qualified">
  <xs:element name="Orders">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Order" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Required" type="xs:string" />
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
        valid = (
            '<Orders xmlns="http://www.spscommerce.com/RSX">'
            "<Order><Required>x</Required></Order></Orders>"
        )
        invalid = '<Orders xmlns="http://www.spscommerce.com/RSX"><Order /></Orders>'
        with tempfile.NamedTemporaryFile("w", suffix=".xsd", delete=False) as tmp:
            tmp.write(xsd)
            path = tmp.name
        try:
            self.assertEqual(rsx.xsd_validate(valid, path), [])
            self.assertTrue(rsx.xsd_validate(invalid, path))
        finally:
            os.unlink(path)

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
        # Carrier tracking only exists with stock_delivery installed.
        has_tracking = "carrier_tracking_ref" in self.picking._fields
        if has_tracking:
            self.picking.carrier_tracking_ref = "1Z999AA10123456784"
        self.picking.date_done = fields.Datetime.now()
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
        shipment_header = header["ShipmentHeader"]
        self.assertEqual(
            shipment_header["ShipmentIdentification"],
            self.picking.name,
        )
        self.assertEqual(shipment_header["TradingPartnerId"], "TP1")
        self.assertEqual(shipment_header["TsetPurposeCode"], "00")
        self.assertIn("ShipNoticeDate", shipment_header)
        if has_tracking:
            self.assertEqual(shipment_header["CarrierProNumber"], "1Z999AA10123456784")
        self.assertEqual(header["Address"][0]["AddressTypeCode"], "ST")
        self.assertEqual(header["Address"][0]["City"], "Springfield")
        order_level = shipment["OrderLevel"][0]
        self.assertEqual(order_level["OrderHeader"]["PurchaseOrderNumber"], "PO-900")
        line = order_level["ItemLevel"][0]["ShipmentLine"]
        self.assertEqual(line["VendorPartNumber"], "SKU-1")
        self.assertEqual(line["GTIN"], "1234567890123")
        self.assertEqual(line["ShipQty"], "10.0")
        self.assertEqual(
            line["ShipQtyUOM"], self.picking.move_ids[:1]._edi_sps_uom_code()
        )

    def test_invoices_template_renders_move(self):
        # The dedicated SPS id wins over Internal Reference.
        self.partner.x_sps_trading_partner_id = "TPX-OUT"
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
        move.invoice_line_ids.tax_ids = self.tax_sale_a.ids
        move.invoice_payment_term_id = self.env["account.payment.term"].create(
            {
                "name": "2% 10 Net 30",
                "discount_percentage": 2.0,
                "discount_days": 10,
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "delay_type": "days_after",
                            "nb_days": 30,
                        }
                    )
                ],
            }
        )
        # Posting generates the tax lines the header Taxes blocks read.
        move.action_post()
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
        self.assertEqual(header["InvoiceHeader"]["TradingPartnerId"], "TPX-OUT")
        self.assertEqual(header["InvoiceHeader"]["InvoiceTypeCode"], "DI")
        self.assertEqual(header["Address"][0]["AddressTypeCode"], "BT")
        self.assertEqual(header["Address"][0]["City"], "Springfield")
        line = invoice["LineItem"][0]["InvoiceLine"]
        self.assertEqual(line["VendorPartNumber"], "SKU-1")
        self.assertEqual(line["InvoiceQty"], "10.0")
        self.assertEqual(line["PurchasePrice"], "12.5")
        terms = header["PaymentTerms"]
        terms = terms[0] if isinstance(terms, list) else terms
        self.assertEqual(terms["TermsNetDueDate"], "2026-12-10")
        self.assertEqual(terms["TermsNetDueDays"], "30")
        self.assertEqual(terms["TermsDescription"], "2% 10 Net 30")
        self.assertEqual(terms["TermsDiscountPercentage"], "2.0")
        self.assertEqual(terms["TermsDiscountDueDays"], "10")
        taxes = header.get("Taxes") or []
        taxes = taxes if isinstance(taxes, list) else [taxes]
        self.assertTrue(taxes)
        self.assertEqual(taxes[0]["TaxPercent"], "15.0")
        self.assertIn("TaxAmount", taxes[0])
        self.assertIn("Description", taxes[0])


class TestSpsOrderImport(TransactionCase):
    def test_order_qty_uom_maps_to_odoo_uom(self):
        """An OrderQtyUOM code resolves to the mapped uom.uom."""
        unit = self.env.ref("uom.product_uom_unit")
        dozen = self.env.ref("uom.product_uom_dozen")
        self.env["res.partner"].create({"name": "SPS Customer", "ref": "TP-UOM"})
        self.env["product.product"].create(
            {
                "name": "UOM Widget",
                "default_code": "UOM-1",
                "uom_id": dozen.id,
            }
        )
        pay_term = self.env["account.payment.term"].create(
            {
                "name": "Net 30",
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "delay_type": "days_after",
                            "nb_days": 30,
                        }
                    )
                ],
            }
        )
        self.env["edi.sps.payment.term.map"].create(
            {"net_days": 30, "payment_term_id": pay_term.id}
        )
        order = {
            "Meta": {
                "SenderUniqueID": "ME",
                "ReceiverUniqueID": "TP-UOM",
                "IsDropShip": "true",
            },
            "Header": {
                "OrderHeader": {
                    "PurchaseOrderNumber": "PO-UOM-1",
                    "TradingPartnerId": "TP-UOM",
                    "CustomerOrderNumber": "CUST-REF-1",
                    "BuyersCurrency": "USD",
                },
                "PaymentTerms": [{"TermsNetDueDays": "30"}],
            },
            "Address": [
                {
                    "AddressTypeCode": "ST",
                    "AddressLocationNumber": "GLN-42",
                    "AddressName": "Dock 4",
                    "Address1": "1 Main St",
                    "City": "Springfield",
                    "State": "IL",
                    "PostalCode": "62701",
                    "Country": "US",
                }
            ],
            "Notes": [{"Note": "Leave at dock."}],
            "LineItem": [
                {
                    "OrderLine": {
                        "LineSequenceNumber": "1",
                        "VendorPartNumber": "UOM-1",
                        "OrderQty": "5",
                        "OrderQtyUOM": "EA",
                        "PurchasePrice": "2.5",
                        "References": [{"ReferenceID": "LINE-REF-9"}],
                    }
                }
            ],
        }
        sale_order = self.env["sale.order"]._edi_sps_import_order(order)
        line = sale_order.order_line[:1]
        self.assertEqual(line.product_uom_id, unit)
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(sale_order.x_sps_location, "GLN-42")
        self.assertEqual(sale_order.x_sps_customer_ref, "CUST-REF-1")
        self.assertTrue(sale_order.x_sps_dropship)
        self.assertEqual(line.x_sps_line_ref, "LINE-REF-9")
        self.assertEqual(sale_order.currency_id.name, "USD")
        self.assertEqual(sale_order.payment_term_id, pay_term)
        self.assertIn("Leave at dock.", sale_order.note)
        ship_to = sale_order.partner_shipping_id
        self.assertEqual(ship_to.type, "delivery")
        self.assertEqual(ship_to.parent_id, sale_order.partner_id)
        self.assertEqual(ship_to.street, "1 Main St")
        self.assertEqual(ship_to.city, "Springfield")
        self.assertEqual(ship_to.x_sps_location, "GLN-42")

        # Same GLN on a later order resolves to the same delivery partner
        # even when the street text differs.
        order2 = copy.deepcopy(order)
        order2["Header"]["OrderHeader"]["PurchaseOrderNumber"] = "PO-UOM-2"
        order2["Address"][0]["Address1"] = "999 Other Rd"
        sale_order2 = self.env["sale.order"]._edi_sps_import_order(order2)
        self.assertEqual(sale_order2.partner_shipping_id, ship_to)
        deliveries = sale_order.partner_id.child_ids.filtered(
            lambda c: c.type == "delivery"
        )
        self.assertEqual(len(deliveries), 1)

    def test_batched_orders_file_splits_per_order(self):
        """A file with several <Order> docs gets one exchange record each."""
        self.env["res.partner"].create({"name": "Split Cust", "ref": "TP-SPLIT"})
        self.env["product.product"].create(
            {"name": "Split Widget", "default_code": "SPLIT-1"}
        )

        def order(po_number):
            return {
                "Meta": {
                    "SenderUniqueID": "ME",
                    "ReceiverUniqueID": "TP-SPLIT",
                },
                "Header": {
                    "OrderHeader": {
                        "PurchaseOrderNumber": po_number,
                        "TradingPartnerId": "TP-SPLIT",
                    }
                },
                "LineItem": [
                    {
                        "OrderLine": {
                            "LineSequenceNumber": "1",
                            "VendorPartNumber": "SPLIT-1",
                            "OrderQty": "2",
                            "OrderQtyUOM": "EA",
                            "PurchasePrice": "1.0",
                        }
                    }
                ],
            }

        backend = self.env.ref("edi_spscommerce.edi_backend_sps")
        record = backend.create_record(
            "sps_orders_in",
            {
                "exchange_filename": "batch.xml",
                "edi_exchange_state": "input_received",
            },
        )
        record._set_file_content(rsx.serialize_orders([order("PO-1"), order("PO-2")]))
        result = self.env["edi.sps.handler"].process(record)
        # The received record imports the first order; the second one is
        # split into a child record that processes through the pipeline.
        self.assertEqual(result.client_order_ref, "PO-1")
        children = record.related_exchange_ids
        self.assertEqual(len(children), 1)
        self.assertEqual(children.parent_id, record)
        self.assertEqual(children.edi_exchange_state, "input_received")
        children.action_exchange_process()
        self.assertEqual(children.record.client_order_ref, "PO-2")

    def test_tset_purpose_codes(self):
        """01 cancels the matching order; 05 replaces it; 07 is a no-op."""
        self.env["res.partner"].create({"name": "Purpose Cust", "ref": "TP-PURP"})
        self.env["product.product"].create(
            {"name": "Purpose Widget", "default_code": "PURP-1"}
        )

        def order(po_number, purpose=None):
            header = {
                "PurchaseOrderNumber": po_number,
                "TradingPartnerId": "TP-PURP",
            }
            if purpose:
                header["TsetPurposeCode"] = purpose
            return {
                "Meta": {"SenderUniqueID": "ME", "ReceiverUniqueID": "TP-PURP"},
                "Header": {"OrderHeader": header},
                "LineItem": [
                    {
                        "OrderLine": {
                            "LineSequenceNumber": "1",
                            "VendorPartNumber": "PURP-1",
                            "OrderQty": "1",
                            "OrderQtyUOM": "EA",
                            "PurchasePrice": "1.0",
                        }
                    }
                ],
            }

        SaleOrder = self.env["sale.order"]
        original = SaleOrder._edi_sps_import_order(order("PO-P1"))
        self.assertEqual(original.state, "draft")

        # 07 duplicate returns the existing order without changes.
        dup = SaleOrder._edi_sps_import_order(order("PO-P1", "07"))
        self.assertEqual(dup, original)

        # 01 cancellation cancels the matching order.
        cancelled = SaleOrder._edi_sps_import_order(order("PO-P1", "01"))
        self.assertEqual(cancelled.state, "cancel")

        # 05 replace imports a fresh draft for the same PO.
        replacement = SaleOrder._edi_sps_import_order(order("PO-P1", "05"))
        self.assertNotEqual(replacement, original)
        self.assertEqual(replacement.state, "draft")
        self.assertEqual(replacement.client_order_ref, "PO-P1")

    def test_order_ack_updates_matching_sale_order(self):
        """An OrderAcks file records ack fields on the matching order."""
        self.env["res.partner"].create({"name": "Ack Cust", "ref": "TP-ACK"})
        self.env["product.product"].create(
            {"name": "Ack Widget", "default_code": "ACK-1"}
        )
        order = {
            "Meta": {"SenderUniqueID": "ME", "ReceiverUniqueID": "TP-ACK"},
            "Header": {
                "OrderHeader": {
                    "PurchaseOrderNumber": "PO-ACK-1",
                    "TradingPartnerId": "TP-ACK",
                }
            },
            "LineItem": [
                {
                    "OrderLine": {
                        "LineSequenceNumber": "1",
                        "VendorPartNumber": "ACK-1",
                        "OrderQty": "1",
                        "OrderQtyUOM": "EA",
                        "PurchasePrice": "1.0",
                    }
                }
            ],
        }
        sale_order = self.env["sale.order"]._edi_sps_import_order(order)

        acks_xml = """<OrderAcks xmlns="http://www.spscommerce.com/RSX">
  <OrderAck><Header><OrderHeader>
    <TradingPartnerId>TP-ACK</TradingPartnerId>
    <PurchaseOrderNumber>PO-ACK-1</PurchaseOrderNumber>
    <AcknowledgementType>BA</AcknowledgementType>
    <AcknowledgementNumber>ACK-77</AcknowledgementNumber>
    <AcknowledgementDate>2026-11-11</AcknowledgementDate>
  </OrderHeader></Header></OrderAck>
  <OrderAck><Header><OrderHeader>
    <TradingPartnerId>TP-ACK</TradingPartnerId>
    <PurchaseOrderNumber>PO-UNKNOWN</PurchaseOrderNumber>
    <AcknowledgementType>BA</AcknowledgementType>
  </OrderHeader></Header></OrderAck>
</OrderAcks>"""
        backend = self.env.ref("edi_spscommerce.edi_backend_sps")
        record = backend.create_record(
            "sps_order_acks_in",
            {
                "exchange_filename": "acks.xml",
                "edi_exchange_state": "input_received",
            },
        )
        record._set_file_content(acks_xml)
        matched = self.env["edi.sps.handler"].process(record)
        # The unmatched ack is skipped; the matched one lands on the SO.
        self.assertEqual(matched, sale_order)
        self.assertEqual(sale_order.x_sps_ack_type, "BA")
        self.assertEqual(sale_order.x_sps_ack_number, "ACK-77")
        self.assertEqual(str(sale_order.x_sps_ack_date), "2026-11-11")

    def test_trading_partner_id_matches_without_ref(self):
        """Inbound orders match partners by x_sps_trading_partner_id."""
        partner = self.env["res.partner"].create(
            {"name": "TPX Cust", "x_sps_trading_partner_id": "TPX-9"}
        )
        self.env["product.product"].create(
            {"name": "TPX Widget", "default_code": "TPX-1"}
        )
        order = {
            "Meta": {"SenderUniqueID": "ME", "ReceiverUniqueID": "TPX-9"},
            "Header": {
                "OrderHeader": {
                    "PurchaseOrderNumber": "PO-TPX-1",
                    "TradingPartnerId": "TPX-9",
                }
            },
            "LineItem": [
                {
                    "OrderLine": {
                        "LineSequenceNumber": "1",
                        "VendorPartNumber": "TPX-1",
                        "OrderQty": "1",
                        "OrderQtyUOM": "EA",
                        "PurchasePrice": "1.0",
                    }
                }
            ],
        }
        sale_order = self.env["sale.order"]._edi_sps_import_order(order)
        self.assertEqual(sale_order.partner_id, partner)
