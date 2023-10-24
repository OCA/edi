# Copyright 2016 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

from odoo.tools import DotDict, file_open


def _get_file_content(filename):
    path = "base_edifact/tests/files/" + filename
    with file_open(path, "rb") as fd:
        return fd.read()


def get_test_data(env):
    ref = env.ref
    return {
        "Retail_EDIFACT_ORDERS_sample1.txt": DotDict(
            {
                "_get_content": partial(
                    _get_file_content, "Retail_EDIFACT_ORDERS_sample1.txt"
                ),
                "client_order_ref": "1AA1TEST",
                "date_order": "2023-06-06",
                "partner": ref("sale_order_import_edifact.partner_edi_invoiceto_dm"),
                "shipping_partner": ref(
                    "sale_order_import_edifact.partner_edi_shipto_dm"
                ),
                # "invoicing_partner": ref(
                #    "sale_order_import_edifact.partner_edi_invoiceto_dm"
                # ),
                # "currency": ref("base.SEK"),
                # "commitment_date": "",
                "products": ref("sale_order_import_edifact.product_product_edifact1_dm")
                + ref("sale_order_import_edifact.product_product_edifact2_dm")
                + ref("sale_order_import_edifact.product_product_edifact3_dm"),
            }
        )
    }


def get_test_data_no_ean_in_lin(env):
    ref = env.ref
    return {
        "test_orders_-_no_ean_in_LIN_segments.txt": DotDict(
            {
                "_get_content": partial(
                    _get_file_content, "test_orders_-_no_ean_in_LIN_segments.txt"
                ),
                "client_order_ref": "467819",
                "date_order": "2023-03-20",
                "partner": ref("sale_order_import_edifact.partner_edi_shipto_dm"),
                "shipping_partner": ref(
                    "sale_order_import_edifact.partner_edi_shipto_dm"
                ),
                "products": ref("sale_order_import_edifact.product_product_edifact4_dm")
                + ref("sale_order_import_edifact.product_product_edifact5_dm")
                + ref("sale_order_import_edifact.product_product_edifact6_dm")
                + ref("sale_order_import_edifact.product_product_edifact7_dm")
                + ref("sale_order_import_edifact.product_product_edifact8_dm"),
                "qty": [12.0, 24.0, 12.0, 24.0, 90.0],
            }
        )
    }
