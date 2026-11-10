# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    # SPS keeps live and test traffic on the same SFTP account; the
    # directory names carry the environment. All four are configurable —
    # get_conn_parameter picks the right one for the backend's test_mode.
    sps_input_dir_pending = fields.Char(
        "SPS input dir (live)",
        default="out",
        help="Directory SPS drops inbound files into; 'out' in production.",
    )
    sps_output_dir_pending = fields.Char(
        "SPS output dir (live)",
        default="in",
        help="Directory outbound files are uploaded to; 'in' in production.",
    )
    sps_test_input_dir_pending = fields.Char(
        "SPS input dir (test)",
        default="testout",
        help="Inbound directory when test_mode is on; 'testout' on SPS.",
    )
    sps_test_output_dir_pending = fields.Char(
        "SPS output dir (test)",
        default="testin",
        help="Outbound directory when test_mode is on; 'testin' on SPS.",
    )

    def _edi_test_mode_supported(self):
        res = super()._edi_test_mode_supported()
        return res or self.backend_type_code == "sps"

    def get_conn_parameter(self, name, operation=None):
        # Route the pending dirs through the SPS live/test convention;
        # everything else (done/error, credentials) resolves normally.
        if self.backend_type_code == "sps" and name in (
            "input_dir_pending",
            "output_dir_pending",
        ):
            test = self.test_mode
            if name == "input_dir_pending":
                return self.sps_test_input_dir_pending if test else self.sps_input_dir_pending
            return self.sps_test_output_dir_pending if test else self.sps_output_dir_pending
        return super().get_conn_parameter(name, operation)
