# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.endpoint.hooks import (  # pylint: disable=odoo-addons-relative-import
    _init_server_action,
)

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    _init_server_action(env)
    domain = [("registry_sync", "=", False)]
    env["endpoint.endpoint"].search(domain).write({"registry_sync": True})
    _logger.info("Activate sync for existing endpoints")
