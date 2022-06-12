# Copyright 2022 Téo Goddet

from openupgradelib import openupgrade

_column_renames = {
    "edi_exchange_record": [("exchange_file", "real_exchange_file")],
}


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(
        env.cr, "edi_exchange_record", "real_exchange_file"
    ):
        openupgrade.rename_columns(env.cr, _column_renames)
