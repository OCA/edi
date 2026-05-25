# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
         ALTER TABLE base_import_pdf_template_line
         ADD COLUMN IF NOT EXISTS sequence INTEGER
         """,
    )
    openupgrade.logged_query(
        env.cr,
        """
         UPDATE base_import_pdf_template_line
         SET sequence = column::integer
         WHERE column IS NOT NULL
         """,
    )
