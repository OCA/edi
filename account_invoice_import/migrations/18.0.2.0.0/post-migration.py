# Copyright 2026 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# In post migration script:
# - we can access the registry
# - the new fields are created
# - the old fields are still readable

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        f"""
        UPDATE res_partner
        SET invoice_import_shrink_lines = (
            SELECT jsonb_object_agg(
                key,
                CASE
                    WHEN value = 'true'::jsonb THEN '"single"'::jsonb
                    ELSE value
                END
            )
            FROM jsonb_each({openupgrade.get_legacy_name("invoice_import_single_line")})
        )
        WHERE {openupgrade.get_legacy_name("invoice_import_single_line")} IS NOT NULL
        """,
    )
