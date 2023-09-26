# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class PunchoutRequest(models.Model):
    _inherit = "punchout.request"

    has_job_access = fields.Boolean(compute="_compute_has_job_access",)
    job_count = fields.Integer(compute="_compute_job_count",)

    @api.depends_context("uid")
    def _compute_has_job_access(self):
        try:
            self.env["queue.job"].check_access_rights("read")
            self.has_job_access = True
        except AccessError:
            self.has_job_access = False

    def _compute_job_count(self):
        job_model = self.env["queue.job"]
        for rec in self:
            rec.job_count = (
                job_model.search_count(rec._get_queue_job_list_domain())
                if rec.has_job_access
                else 0
            )

    def _get_queue_job_description(self):
        self.ensure_one()
        return f"Import of Purchase Order through Punchout request {self.display_name}"

    def _get_queue_job_list_domain(self):
        self.ensure_one()
        return [
            ("name", "=", self._get_queue_job_description()),
        ]

    def action_show_job_list(self):
        self.ensure_one()
        action = self.env.ref("queue_job.action_queue_job").read([])[0]
        action.update({"domain": self._get_queue_job_list_domain(), "context": {}})
        return action

    def _store_punchout_request(self, *args, **kwargs):
        request = super()._store_punchout_request(*args, **kwargs)
        if request:
            request.with_user(request.user_id).with_delay(
                description=request._get_queue_job_description()
            ).action_process()
        return request
