# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests import common


class TestVoxelStockPicking(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestVoxelStockPicking, cls).setUpClass()
        # Sale order company
        country = cls.env["res.country"].create({"name": "Country", "code": "CT"})
        state = cls.env["res.country.state"].create(
            {"name": "Province", "code": "PRC", "country_id": country.id}
        )
        main_company = cls.env.ref("base.main_company")
        main_company.write(
            {
                "vat": "US1234567890",
                "street": "Street 1",
                "street2": "Street 2",
                "name": "YourCompany",
                "city": "City",
                "zip": "99999",
                "state_id": state.id,
                "country_id": country.id,
                "email": "info@yourcompany.example.com",
            }
        )
        # Sale order client
        partner = cls.env["res.partner"].create(
            {
                "ref": "C01",
                "vat": "BE0123456789",
                "name": "Client (test)",
                "email": "client_test@example.com",
                "street": "Street 1",
                "street2": "Street 2",
                "city": "City (test)",
                "zip": "10000",
                "state_id": cls.env.ref("base.state_us_49").id,
                "country_id": cls.env.ref("base.us").id,
            }
        )
        product = cls.env["product.product"].create(
            {"default_code": "DC_001", "name": "Product 1 (test)", "type": "product"}
        )
        cls.env["product.customerinfo"].create(
            {
                "name": partner.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "1234567891234",
            }
        )
        product2 = cls.env["product.product"].create(
            {
                "default_code": "DC_002",
                "name": "Product 2 (test)",
                "type": "product",
                "tracking": "lot",
            }
        )
        lot = cls.env["stock.production.lot"].create(
            {
                "name": "LOT01",
                "product_id": product2.id,
                "life_date": "2020-01-01 12:05:23",
                "company_id": main_company.id,
            }
        )
        sale_order = cls.env["sale.order"].create(
            {
                "name": "Sale order name (test)",
                "partner_id": partner.id,
                "company_id": main_company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 2,
                            "product_uom": product.uom_id.id,
                            "price_unit": 750,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": product2.id,
                            "product_uom_qty": 1,
                            "product_uom": product2.uom_id.id,
                            "price_unit": 50,
                        },
                    ),
                ],
            }
        )
        # Confirm quotation
        sale_order.action_confirm()
        # Validate picking
        cls.picking = sale_order.picking_ids
        cls.picking.write(
            {
                "name": "Picking name (test)",
                "date": datetime(2020, 1, 7),
                "company_id": main_company.id,
                "note": "Picking note (test)",
            }
        )
        cls.picking.move_lines[0].write({"quantity_done": 2})
        cls.picking.move_lines[1].write({"quantity_done": 1})
        cls.picking.move_lines[1].move_line_ids.lot_id = lot.id
        cls.picking.button_validate()

    def test_get_voxel_filename(self):
        bef = datetime.now()
        bef = datetime(
            bef.year,
            bef.month,
            bef.day,
            bef.hour,
            bef.minute,
            bef.second,
            (bef.microsecond // 1000) * 1000,
        )
        filename = self.picking._get_voxel_filename()
        document_type, date_time = filename[:-4].split("_", 1)
        date_time = datetime.strptime(date_time, "%Y%m%d_%H%M%S_%f")
        self.assertEqual(document_type, "Albaran")
        self.assertGreaterEqual(date_time, bef)

    def test_get_report_values(self):
        # Get report data
        model_name = "report.edi_voxel_stock_picking.template_voxel_picking"
        report_edi_obj = self.env[model_name]
        report_data = report_edi_obj._get_report_values(self.picking.ids)
        # Get expected data
        expected = self._get_picking_data()
        # Check data
        self.assertDictEqual(report_data["general"], expected["general"])
        self.assertDictEqual(report_data["supplier"], expected["supplier"])
        self.assertDictEqual(report_data["client"], expected["client"])
        self.assertListEqual(report_data["customers"], expected["customers"])
        self.assertListEqual(report_data["comments"], expected["comments"])
        self.assertListEqual(report_data["references"], expected["references"])
        self.assertListEqual(report_data["products"], expected["products"])

    def _get_picking_data(self):
        return {
            "general": self._get_general_data(),
            "supplier": self._get_suplier_data(),
            "client": self._get_client_data(),
            "customers": self._get_customers_data(),
            "comments": self._get_comments_data(),
            "references": self._get_references_data(),
            "products": self._get_products_data(),
        }

    # report data. Auxiliary methods
    # ------------------------------
    def _get_general_data(self):
        return {
            "Type": "AlbaranComercial",
            "Ref": "Picking name (test)",
            "Date": "2020-01-07",
        }

    def _get_suplier_data(self):
        return {
            "CIF": "US1234567890",
            "Company": "YourCompany",
            "Address": "Street 1, Street 2",
            "City": "City",
            "PC": "99999",
            "Province": "Province",
            "Country": "CT",
            "Email": "info@yourcompany.example.com",
        }

    def _get_client_data(self):
        return {
            "SupplierClientID": "C01",
            "CIF": "BE0123456789",
            "Company": "Client (test)",
            "Address": "Street 1, Street 2",
            "City": "City (test)",
            "PC": "10000",
            "Province": "West Virginia",
            "Country": "USA",
            "Email": "client_test@example.com",
        }

    def _get_customers_data(self):
        return [
            {
                "SupplierClientID": "C01",
                "SupplierCustomerID": "C01",
                "Customer": "Client (test)",
                "Address": "Street 1, Street 2",
                "City": "City (test)",
                "PC": "10000",
                "Province": "West Virginia",
                "Country": "USA",
                "Email": "client_test@example.com",
            }
        ]

    def _get_comments_data(self):
        return [{"Msg": "Picking note (test)"}]

    def _get_references_data(self):
        return [{"PORef": "Sale order name (test)"}]

    def _get_products_data(self):
        return [
            {
                "product": {
                    "SupplierSKU": "DC_001",
                    "CustomerSKU": "1234567891234",
                    "Item": "Product 1 (test)",
                    "Qty": "2.0",
                    "MU": "Unidades",
                },
            },
            {
                "product": {
                    "SupplierSKU": "DC_002",
                    "CustomerSKU": False,
                    "Item": "Product 2 (test)",
                    "Qty": "1.0",
                    "MU": "Unidades",
                    "TraceabilityList": [
                        {
                            "BatchNumber": "LOT01",
                            "ExpirationDate": "2020-01-01T12:05:23",
                            "Quantity": 1.0,
                        }
                    ],
                },
            },
        ]
