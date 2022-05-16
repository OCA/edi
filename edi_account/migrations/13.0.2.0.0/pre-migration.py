# Copyright 2022 Creu Blanca - Alba Riera

from openupgradelib import openupgrade

_column_renames = {
    "account_move": [("disable_edi_auto", "edi_auto_disabled")],
}


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "account_move", "disable_edi_auto"):
        openupgrade.rename_columns(env.cr, _column_renames)
