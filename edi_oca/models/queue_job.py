# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = 'queue.job'

    def write(self, vals):
        for job in self:
            records = job.records.exists()
            if len(records) != 1 or records._name != "edi.exchange.record":
                continue
            if (vals.get("state", "") == "failed" and records.is_queued
                    and job.state != "failed"):
                records.is_queued = False
        return super().write(vals)
