# Copyright 2016 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

from odoo.tools import DotDict, file_open


def _get_file_content(filename):
    path = "sale_order_import_ubl/tests/files/" + filename
    with file_open(path, "rb") as fd:
        return fd.read()


def get_test_data(env):
    ref = env.ref
    return {
        "UBL-Order-2.1-Example.xml": DotDict(
            {
                "_get_content": partial(_get_file_content, "UBL-Order-2.1-Example.xml"),
                "client_order_ref": "34",
                "date_order": "2010-01-20",
                "partner": ref("sale_order_import_ubl.svensson"),
                "shipping_partner": ref("sale_order_import_ubl.swedish_trucking"),
                "invoicing_partner": ref("sale_order_import_ubl.karlsson"),
                "currency": ref("base.SEK"),
                "commitment_date": "2010-02-26 18:00:00",
                "products": ref("sale_order_import_ubl.product_red_paint")
                + ref("sale_order_import_ubl.product_pencil"),
            }
        ),
        "UBL-Order-2.0-Example.xml": DotDict(
            {
                "_get_content": partial(_get_file_content, "UBL-Order-2.0-Example.xml"),
                "client_order_ref": "AEG012345",
                "date_order": "2010-06-20",
                "partner": ref("sale_order_import_ubl.fred_churchill"),
                "shipping_partner": ref("sale_order_import_ubl.iyt"),
                "currency": ref("base.GBP"),
                "commitment_date": "2010-02-26 00:00:00",
                "products": ref("sale_order_import_ubl.product_beeswax"),
            }
        ),
        "UBL-RequestForQuotation-2.0-Example.xml": DotDict(
            {
                "_get_content": partial(
                    _get_file_content, "UBL-RequestForQuotation-2.0-Example.xml"
                ),
                "partner": ref("sale_order_import_ubl.s_massiah"),
                "shipping_partner": ref("sale_order_import_ubl.iyt"),
                "products": ref("sale_order_import_ubl.product_beeswax"),
            }
        ),
        "UBL-RequestForQuotation-2.1-Example.xml": DotDict(
            {
                "_get_content": partial(
                    _get_file_content, "UBL-RequestForQuotation-2.1-Example.xml"
                ),
                "partner": ref("sale_order_import_ubl.gentofte_kommune"),
                "currency": ref("base.DKK"),
                "shipping_partner": ref(
                    "sale_order_import_ubl.delivery_gentofte_kommune"
                ),
                "products": ref("product.product_product_25")
                + ref("product.product_product_24")
                + ref("product.product_product_9"),
            }
        ),
    }
