# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import base64
from datetime import datetime
from unittest.mock import patch

from lxml import etree as ElementTree

from odoo.tools.misc import file_open, file_path

from odoo.addons.edi_ediversa_oca.components.ediversa_api import EdiversaApi
from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class TestEdiEdiversaSaleOrderImport(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.company = cls.env.company.write(
            {
                "use_edi_ediversa": True,
                "edi_ediversa_test": True,
                "edi_ediversa_user": "test",
                "edi_ediversa_password": "test",
            }
        )
        cls.account_tax = cls.env["account.tax"].create(
            {
                "name": "Tax 10%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 10.0,
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "barcode": "11111111"}
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test-Customer",
                "ediversa_id": "1000000000",
                "child_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test-Customer Invoice",
                            "type": "invoice",
                            "ediversa_id": "1000000000",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test-Customer Shipping",
                            "type": "delivery",
                            "ediversa_id": "1000000000",
                        },
                    ),
                ],
            }
        )
        return res

    def get_documents(self, company):
        response = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Body><downloadDocumentListExtendedResponse xmlns="comedicloudwstest">
<result><status xsi:type="xsd:string">OK</status>
<documents soapenc:arrayType="xsd:anyType[2]" xsi:type="soapenc:Array">
<document><id xsi:type="xsd:string">test_ediversa_1</id>
<sender_identifier xsi:type="xsd:long">11111111</sender_identifier>
<sender_name xsi:type="xsd:base64Binary">TEST-1</sender_name>
<receiver_identifier xsi:type="xsd:long">22222222</receiver_identifier>
<receiver_name xsi:type="xsd:string">Test Company</receiver_name>
<process_date xsi:type="xsd:dateTime">2025-06-16T08:19:17Z</process_date>
<type xsi:type="xsd:string">ORDERS</type><format xsi:type="xsd:string">
PLANO</format><document_number xsi:type="xsd:int">000000001</document_number>
</document><document><id xsi:type="xsd:string">test_ediversa_2</id>
<sender_identifier xsi:type="xsd:long">33333333</sender_identifier>
<sender_name xsi:type="xsd:string">TEST-2</sender_name>
<receiver_identifier xsi:type="xsd:long">44444444</receiver_identifier>
<receiver_name xsi:type="xsd:string">Test Company</receiver_name>
<process_date xsi:type="xsd:dateTime">2025-06-16T08:19:18Z</process_date>
<type xsi:type="xsd:string">ORDERS</type><format xsi:type="xsd:string">PLANO
</format><document_number xsi:type="xsd:string">000000002</document_number>
</document></documents></result></downloadDocumentListExtendedResponse>
</soap:Body></soap:Envelope>"""
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": "comedicloudwstest",
        }
        tree = ElementTree.fromstring(response)
        result = tree.findall(
            "./soap:Body"
            "/a:downloadDocumentListExtendedResponse"
            "/a:result"
            "/a:documents"
            "/a:document",
            namespaces,
        )
        return result

    def download_document_new_partner(self, identifier, company):
        path = file_path(
            "edi_ediversa_oca_sale_order_import/tests/sale_order_docs/ediversa_sale_order_new_partner.txt"
        )
        data = base64.b64encode(file_open(path, "rb").read()).decode()
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Body><downloadDocumentResponse
xmlns="comedicloudwstest"><result>
<status xsi:type="xsd:string">OK</status>
<documents soapenc:arrayType="xsd:anyType[1]"
xsi:type="soapenc:Array"><document><name xsi:type="xsd:string">
ORDERS_000104100024621_20250616114315.txt</name>
<mimeType xsi:type="xsd:string">text/plain</mimeType>
<encoding xsi:type="xsd:string">ISO-8859-1</encoding>
<type xsi:type="xsd:string">ORDERS</type><content xsi:type="xsd:string">
{data}</content></document></documents></result>
</downloadDocumentResponse></soap:Body></soap:Envelope>"""
        response = response.encode()
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": "comedicloudwstest",
        }
        tree = ElementTree.fromstring(response)
        doc = tree.find("./soap:Body" "//a:content", namespaces)
        return doc

    def download_document_existing_partner(self, identifier, company):
        path = file_path(
            "edi_ediversa_oca_sale_order_import/tests/sale_order_docs/ediversa_sale_order_existing_partner.txt"
        )
        data = base64.b64encode(file_open(path, "rb").read()).decode()
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Body><downloadDocumentResponse
xmlns="comedicloudwstest"><result>
<status xsi:type="xsd:string">OK</status>
<documents soapenc:arrayType="xsd:anyType[1]"
xsi:type="soapenc:Array"><document><name xsi:type="xsd:string">
ORDERS_000104100024621_20250616114315.txt</name>
<mimeType xsi:type="xsd:string">text/plain</mimeType>
<encoding xsi:type="xsd:string">ISO-8859-1</encoding>
<type xsi:type="xsd:string">ORDERS</type><content xsi:type="xsd:string">
{data}</content></document></documents></result>
</downloadDocumentResponse></soap:Body></soap:Envelope>"""
        response = response.encode()
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": "comedicloudwstest",
        }
        tree = ElementTree.fromstring(response)
        doc = tree.find("./soap:Body" "//a:content", namespaces)
        return doc

    def create_exchange_record(self):
        company = self.env.company
        exchange_type = self.env.ref(
            "edi_ediversa_oca_sale_order_import.ediversa_sale_input_exchange_type"
        )
        backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
        return self.env["edi.exchange.record"].create(
            {
                "company_id": company.id,
                "external_identifier": "test_ediversa",
                "type_id": exchange_type.id,
                "direction": "input",
                "edi_exchange_state": "input_pending",
                "backend_id": backend.id,
            }
        )

    def check_invoice_common_vals(self, edi_exchange_record):
        self.assertTrue(edi_exchange_record.exchange_file)
        self.assertEqual(edi_exchange_record.edi_exchange_state, "input_processed")
        sale_order = self.env[edi_exchange_record.model].search(
            [("id", "=", edi_exchange_record.res_id)], limit=1
        )
        self.assertTrue(sale_order)
        self.assertEqual(sale_order.order_line[0].product_id.barcode, "11111111")
        self.assertEqual(sale_order.order_line[0].product_uom_qty, 10)
        self.assertEqual(sale_order.order_line[0].price_unit, 50)
        self.assertEqual(sale_order.date_order, datetime.strptime("20250101", "%Y%m%d"))
        self.assertEqual(
            sale_order.commitment_date, datetime.strptime("20250201", "%Y%m%d")
        )

    def test_ediversa_create_exchange_record(self):
        with patch.object(
            EdiversaApi,
            "get_documents",
            self.get_documents,
        ):
            self.env["edi.exchange.record"]._cron_ediversa_import_sales()
            exchange_type = self.env.ref(
                "edi_ediversa_oca_sale_order_import.ediversa_sale_input_exchange_type"
            )
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            edi_record_1 = self.env["edi.exchange.record"].search(
                [("external_identifier", "=", "test_ediversa_1")], limit=1
            )
            self.assertTrue(edi_record_1)
            self.assertEqual(edi_record_1.type_id, exchange_type)
            self.assertEqual(edi_record_1.backend_id, backend)
            edi_record_2 = self.env["edi.exchange.record"].search(
                [("external_identifier", "=", "test_ediversa_2")], limit=1
            )
            self.assertTrue(edi_record_2)
            self.assertEqual(edi_record_2.type_id, exchange_type)
            self.assertEqual(edi_record_2.backend_id, backend)

    def test_ediversa_sale_order_new_partner(self):
        with patch.object(
            EdiversaApi,
            "download_document",
            self.download_document_new_partner,
        ):
            edi_exchange_record = self.create_exchange_record()
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            self.assertTrue(edi_exchange_record)
            backend._cron_check_input_exchange_sync()
            self.check_invoice_common_vals(edi_exchange_record)
            sale_order = self.env[edi_exchange_record.model].search(
                [("id", "=", edi_exchange_record.res_id)], limit=1
            )
            customer = self.env["res.partner"].search(
                [("ediversa_id", "=", "000000002")], limit=1
            )
            delivery_address = self.env["res.partner"].search(
                [("ediversa_id", "=", "000000003")], limit=1
            )
            invoice_address = self.env["res.partner"].search(
                [("ediversa_id", "=", "000000004")], limit=1
            )
            self.assertEqual(sale_order.partner_id, customer)
            self.assertEqual(sale_order.partner_shipping_id, delivery_address)
            self.assertEqual(sale_order.partner_invoice_id, invoice_address)

    def test_ediversa_sale_order_existing_partner(self):
        with patch.object(
            EdiversaApi,
            "download_document",
            self.download_document_existing_partner,
        ):
            edi_exchange_record = self.create_exchange_record()
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            self.assertTrue(edi_exchange_record)
            backend._cron_check_input_exchange_sync()
            self.check_invoice_common_vals(edi_exchange_record)
            sale_order = self.env[edi_exchange_record.model].search(
                [("id", "=", edi_exchange_record.res_id)], limit=1
            )
            delivery_address = self.customer.child_ids.filtered(
                lambda p: p.type == "delivery"
            )
            invoice_address = self.customer.child_ids.filtered(
                lambda p: p.type == "invoice"
            )
            self.assertEqual(sale_order.partner_id, self.customer)
            self.assertEqual(sale_order.partner_shipping_id, delivery_address)
            self.assertEqual(sale_order.partner_invoice_id, invoice_address)
