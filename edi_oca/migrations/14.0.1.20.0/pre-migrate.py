# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Backup old style rules to be used later on post migrate
    old_table = "edi_exchange_type_ir_model_rel"
    if not tools.sql.table_exists(cr, old_table):
        return
    bkp_table = "exc_type_model_rel_bkp"
    if tools.sql.table_exists(cr, bkp_table):
        return

    bkp_query = """
    CREATE TABLE IF NOT EXISTS
        exc_type_model_rel_bkp
    AS
        SELECT
            rel.ir_model_id as model_id,
            type.id as type_id,
            type.enable_domain as enable_domain,
            type.enable_snippet as enable_snippet,
            type.model_manual_btn as form_btn
        FROM
            edi_exchange_type type,
            edi_exchange_type_ir_model_rel rel
        WHERE
            rel.edi_exchange_type_id = type.id;
    """
    cr.execute(bkp_query)

    _logger.info("edi.exchange.type old style rules backed up")
