# Copyright 2022 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from functools import partial

from odoo.tools import DotDict, file_open


def _as_base64(filename):
    path = f"product_import_ubl/tests/files/{filename}"
    with file_open(path, "rb") as fobj:
        data = fobj.read()
    return base64.b64encode(data)


def get_test_data(env):
    ref = env.ref
    return {
        "UBL-Catalogue_Example.xml": DotDict(
            {
                "_as_base64": partial(_as_base64, "UBL-Catalogue_Example.xml"),
                "products": [
                    {
                        "active": True,
                        "name": "Copy paper",
                        "code": "MNTR011",
                        "barcode": False,
                        "product_code": "MNTR01349087911",
                        "description": "Photo copy paper 80g A4, package of 500 sheets.",
                        "uom": ref("uom.product_uom_lb"),
                        "currency": ref("base.EUR"),
                        "min_qty": 1.0,
                        "price": 10.0,
                        "company": False,
                    },
                    {
                        "active": True,
                        "name": "Copy paper",
                        "code": "MNTR012",
                        "barcode": False,
                        "product_code": "MNTR01349087912",
                        "description": (
                            "Photo copy paper 80g A4, carton of 10 units "
                            "with 500 sheets each"
                        ),
                        "uom": ref("uom.product_uom_unit"),
                        "currency": ref("base.EUR"),
                        "min_qty": 0.0,
                        "price": 90.0,
                        "company": False,
                    },
                ],
            }
        ),
        "UBL-Catalogue_Example2.xml": DotDict(
            {
                "_as_base64": partial(_as_base64, "UBL-Catalogue_Example2.xml"),
                "products": [
                    {
                        "active": True,
                        "name": "First product",
                        "code": "998000924",
                        "barcode": "1234567890924",
                        "product_code": "BOCAP-B",
                        "description": False,
                        "uom": ref("uom.product_uom_unit"),
                        "currency": ref("base.EUR"),
                        "min_qty": 1.0,
                        "price": 1.35,
                        "company": ref("base.main_company"),
                    },
                    {
                        "active": True,
                        "name": "Copy paper",
                        "code": "MNTR011X1",
                        "barcode": "1234567890114",
                        "product_code": "MNTR01349087911",
                        "description": "Photo copy paper 80g A4, package of 500 sheets.",
                        "uom": ref("uom.product_uom_unit"),
                        "currency": ref("base.EUR"),
                        "min_qty": 1.0,
                        "price": 12.55,
                        "company": ref("base.main_company"),
                    },
                    {
                        "active": True,
                        "name": "Copy paper",
                        "code": "MNTR012X2",
                        "barcode": "1234567890124",
                        "product_code": "MNTR01349087912",
                        "description": (
                            "Photo copy paper 80g A4, carton of 10 units "
                            "with 500 sheets each"
                        ),
                        "uom": ref("uom.product_uom_unit"),
                        "currency": ref("base.EUR"),
                        "min_qty": 20.0,
                        "price": 91.5,
                        "company": ref("base.main_company"),
                    },
                    {
                        "active": False,
                        "name": "Copy paper, outdated",
                        "code": "MNTR010X9",
                        "barcode": False,
                        "product_code": False,
                        "description": False,
                        "uom": ref("uom.product_uom_unit"),
                        "currency": ref("base.USD"),
                        "min_qty": 0.0,
                        "price": 0.0,
                        "company": ref("base.main_company"),
                    },
                ],
            }
        ),
    }
