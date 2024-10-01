# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from odoo.addons.component.core import Component


class EDIExchangeEDIFACTInput(Component):

    _name = "edi.input.process.edifact.input"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.edifact.input"

    def process(self):
        """Process incoming EDIFACT record and confirm record."""
        file_content = self.exchange_record._get_file_content()
        wizard = self.env["purchase.order.import"].create({
            "import_type": "edifact",
            "order_file": base64.b64encode(file_content.encode()),
            "order_filename": self.exchange_record.exchange_filename
        })
        action = wizard.import_order_button()
        return action
