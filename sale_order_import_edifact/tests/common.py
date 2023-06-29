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
