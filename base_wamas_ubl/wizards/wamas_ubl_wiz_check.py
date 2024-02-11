# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from base64 import b64decode

from odoo import _, api, fields, models


class WamasUblWizCheck(models.TransientModel):
    _name = "wamas.ubl.wiz.check"
    _description = "Check WAMAS File Wizard"

    wamas_file = fields.Binary(
        "WAMAS File",
        required=True,
    )
    wamas_filename = fields.Char("WAMAS Filename")
    output = fields.Text()
    supported_telegram = fields.Text(
        default=lambda self: ", ".join(
            self.env["base.wamas.ubl"].get_supported_telegram()
        )
    )

    @api.onchange("wamas_filename")
    def _onchange_wamas_filename(self):
        self.output = False

    def btn_check(self):
        self.ensure_one()
        wamas_file_decoded = b64decode(self.wamas_file).decode("iso-8859-1")

        bwu_obj = self.env["base.wamas.ubl"]
        try:
            wamas_type = bwu_obj.get_wamas_type(wamas_file_decoded)
            data = bwu_obj.wamas2dict(wamas_file_decoded)

            self.output = (
                _(
                    """- WAMAS Type: %(wamas_type)s
- Data: %(data)s"""
                )
                % dict(
                    wamas_type=wamas_type,
                    data=json.dumps(data, indent=4, sort_keys=False),
                )
            )
        except Exception as e:
            self.output = _("""- Error: %s""") % (e)

        return {
            "view_mode": "form",
            "res_model": "wamas.ubl.wiz.check",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
