# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Rename table for recreating m2m relation
    openupgrade.rename_tables(
        env.cr, [("account_invoice_voxel_job_rel", "old_invoice_voxel_job_rel")]
    )
