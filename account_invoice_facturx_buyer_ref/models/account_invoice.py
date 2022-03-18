# Copyright 2021 Camptocamp
# @author: Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def _cii_trade_agreement_buyer_ref(self, partner):
        return (
            partner.facturx_ref
            or partner.commercial_partner_id.facturx_ref
            or super()._cii_trade_agreement_buyer_ref(partner)
        )
