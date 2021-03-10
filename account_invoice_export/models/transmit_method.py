# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import fields, models


class TransmitMethod(models.Model):
    _inherit = "transmit.method"

    send_through_http = fields.Boolean(
        string="Enable send eBill", help="Adds a Send eBill button on the invoice"
    )
    destination_url = fields.Char(string="Url")
    destination_user = fields.Char(string="User", copy=False)
    destination_pwd = fields.Char(string="Password", copy=False)

    def get_transmission_http_header(self):
        """Generate the HTTP header needed by the transmission method.

        For now only basic authentication is implemented.

        """
        self.ensure_one()
        auth = "{}:{}".format(
            self.destination_user,
            self.destination_pwd,
        )
        auth64 = base64.encodebytes(auth.encode("ascii"))[:-1]
        return {"Authorization": "Basic " + auth64.decode("utf-8")}
