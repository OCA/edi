# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

import pytz

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    voxel_enabled = fields.Boolean(string="Enable Voxel")
    voxel_send_mode = fields.Selection(
        string="Send mode",
        selection=[
            ("auto", "On validate"),
            ("fixed", "At fixed time"),
            ("delayed", "With delay"),
        ],
        default="auto",
    )
    voxel_sent_time = fields.Float(string="Sent time")
    voxel_delay_time = fields.Float(string="Delay time")
    voxel_login_ids = fields.One2many(
        comodel_name="voxel.login", inverse_name="company_id", string="Voxel logins",
    )

    def _get_voxel_report_eta(self):
        if self.voxel_send_mode == "fixed":
            tz = self.env.context.get("tz", self.env.user.partner_id.tz)
            offset = datetime.now(pytz.timezone(tz)).strftime("%z") if tz else "+00"
            hour_diff = int(offset[:3])
            hour, minute = divmod(self.voxel_sent_time * 60, 60)
            hour = int(hour - hour_diff)
            minute = int(minute)
            now = datetime.now()
            if now.hour > hour or (now.hour == hour and now.minute > minute):
                now += timedelta(days=1)
            now = now.replace(hour=hour, minute=minute)
            return now
        elif self.voxel_send_mode == "delayed":
            return datetime.now() + timedelta(hours=self.voxel_delay_time)
        else:
            return None
