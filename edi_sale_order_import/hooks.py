# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)


def deprecate():
    _logger.warning("`edi_sale_order_import` is deprecated. Use `edi_sale_oca`")


def post_load_hook():
    deprecate()
