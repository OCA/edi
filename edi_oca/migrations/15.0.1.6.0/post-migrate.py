# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api, tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    bkp_table = "exc_type_model_rel_bkp"
    if not tools.sql.table_exists(cr, bkp_table):
        return

    # Use backup table (created by pre-migrate step) to create type rules
    env = api.Environment(cr, SUPERUSER_ID, {})
    query = """
        SELECT * FROM exc_type_model_rel_bkp
    """
    cr.execute(query)
    res = cr.dictfetchall()
    model = env["edi.exchange.type.rule"]
    for item in res:
        kind = "form_btn" if item.pop("form_btn", False) else "custom"
        vals = dict(item, name="Default", kind=kind)
        rec = model.create(vals)
        rec.type_id.button_wipe_deprecated_rule_fields()

    cr.execute("DROP TABLE exc_type_model_rel_bkp")
    _logger.info("edi.exchange.type.rule created")
