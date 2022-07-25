# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

# fmt: off
from odoo.addons.endpoint_route_handler.registry import (
    EndpointRegistry,  # pylint: disable=odoo-addons-relative-import
)

# fmt: on

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    EndpointRegistry._setup_table(cr)
