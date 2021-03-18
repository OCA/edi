# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class TransmitMethod(models.Model):
    _name = "transmit.method"
    _inherit = ["transmit.method", "server.env.mixin"]

    _server_env_section_name_field = "code"

    @property
    def _server_env_fields(self):
        return {
            "destination_user": {},
            "destination_pwd": {},
            "destination_url": {},
        }
