# Copyright 2023 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

mapping_channel_record_data = {
    "voxel_export": "channel_voxel_export",
    "voxel_import": "channel_voxel_import",
    "voxel_status": "channel_voxel_status",
}


@openupgrade.migrate()
def migrate(env, version):
    vals_list = []
    domain = [
        ("name", "in", list(mapping_channel_record_data.keys())),
        ("parent_id", "=", env.ref("queue_job.channel_root").id),
    ]
    for channel in env["queue.job.channel"].search(domain):
        vals_list.append(
            {
                "noupdate": True,
                "name": mapping_channel_record_data[channel.name],
                "module": "edi_voxel_oca",
                "model": "queue.job.channel",
                "res_id": channel.id,
            }
        )
    env["ir.model.data"].create(vals_list)
