# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    def _edi_test_mode_supported(self):
        res = super()._edi_test_mode_supported()
        return res or self.backend_type_code == "sps"
