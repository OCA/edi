# Copyright 2022 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from .registry import EndpointRegistry

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    # this is the trigger that sends notifications when jobs change
    _logger.info("Create table")
    EndpointRegistry._setup_table(cr)
