# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PunchoutBackend(models.Model):
    _inherit = "punchout.backend"

    # OCI-specific fields
    oci_version = fields.Selection(
        [("3.0", "3.0"), ("4.0", "4.0"), ("5.0", "5.0")],
        default="5.0",
        string="OCI Version",
    )
    oci_custom_parameters = fields.Char(
        string="Vendor-specific parameters",
        groups="base.group_system",
        help="Authentication parameters in query string format: "
        "username=user&password=pass",
    )

    @api.model
    def _selection_protocol(self):
        """Add OCI to available protocols."""
        res = super()._selection_protocol()
        res.append(("oci", "OCI"))
        return res
