# Copyright 2023 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    mapping_function_record_data = {
        (
            "_get_and_send_voxel_report",
            env.ref("edi_voxel_oca.channel_voxel_export").id,
        ): "job_function_get_and_send_voxel_report",
        (
            "_update_error_status",
            env.ref("edi_voxel_oca.channel_voxel_status").id,
        ): "job_function_update_error_status",
    }
    vals_list = []
    domain = [("model_id", "=", env.ref("account.model_account_move").id)]
    function = env["queue.job.function"].search(domain)
    for record in function:
        key = (record.method, record.channel_id.id)
        if key in mapping_function_record_data:
            vals_list.append(
                {
                    "noupdate": True,
                    "name": mapping_function_record_data[key],
                    "module": "edi_voxel_account_invoice_oca",
                    "model": "queue.job.function",
                    "res_id": record.id,
                }
            )
    env["ir.model.data"].create(vals_list)
