# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PunchoutBackend(models.Model):
    _name = "punchout.backend"
    _inherit = ["punchout.backend", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        return {
            "url": {},
            "from_domain": {},
            "from_identity": {},
            "to_domain": {},
            "to_identity": {},
            "shared_secret": {},
            "user_agent": {},
            "deployment_mode": {},
            "browser_form_post_url": {},
        }
