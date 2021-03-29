# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """UPDATE account_move am
        SET voxel_state = ai.voxel_state,
            voxel_xml_report = ai.voxel_xml_report,
            voxel_filename = ai.voxel_filename,
            processing_error = ai.processing_error
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """INSERT INTO account_invoice_voxel_job_rel
        (invoice_id, voxel_job_id)
        SELECT am.id, rel.voxel_job_id
        FROM old_invoice_voxel_job_rel rel
        JOIN account_move am ON am.old_invoice_id = rel.invoice_id""",
    )
