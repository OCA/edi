# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    # For backward compat, enable buttons on all exc types that had a model conf.
    domain = [("model_ids", "!=", False), ("model_manual_btn", "=", False)]
    env["edi.exchange.type"].search(domain).write({"model_manual_btn": True})
    _logger.info("Activate model manual button on existing `edi.exchange.type`")
