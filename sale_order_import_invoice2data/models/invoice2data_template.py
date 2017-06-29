# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
from openerp import api, fields, models


class Invoice2dataTemplate(models.Model):
    _inherit = 'invoice2data.template'

    template_type = fields.Selection(
        selection_add=[('sale_order', 'Sale order')],
    )

    @api.multi
    def _preview_sale_order(self):
        return self._dict2html(
            self.env['sale.order.import'].parse_pdf_order(
                base64.b64decode(self.preview_file)
            )
        )
