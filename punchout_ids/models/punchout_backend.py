# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PunchoutBackend(models.Model):
    _inherit = "punchout.backend"

    # IDS-specific fields
    ids_version = fields.Selection(
        [("1.3", "1.3"), ("2.5", "2.5")],
        default="2.5",
        string="IDS Version",
    )
    ids_name_kunde = fields.Char(
        string="Customer Name",
        help="IDS parameter 'name_kunde'",
    )
    ids_kndnr = fields.Char(
        string="Customer Number",
        help="IDS parameter 'kndnr'",
    )
    ids_pw_kunde = fields.Char(
        string="Customer Password",
        groups="base.group_system",
        help="IDS parameter 'pw_kunde'",
    )

    @api.model
    def _selection_protocol(self):
        """Add IDS to available protocols."""
        res = super()._selection_protocol()
        res.append(("ids", "IDS"))
        return res
