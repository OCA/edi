# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    # Find and drop endpoint XID to avoid losing the endpoint if used.
    rec = env["ir.model.data"].search(
        [
            ("name", "=", "endpoint_demo_1"),
            ("module", "=", "edi_sale_order_import_ubl_endpoint"),
        ]
    )
    if rec:
        _logger.info("Drop xmlid for edi_sale_order_import_ubl_endpoint endpoint")
        rec.unlink()
    return
