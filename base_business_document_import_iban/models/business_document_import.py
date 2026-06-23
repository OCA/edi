# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import ValidationError

from odoo.addons.base_iban.models.res_partner_bank import normalize_iban, validate_iban


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _match_partner_bank(
        self, partner, iban, bic, chatter_msg, create_if_not_found=False
    ):
        normalized_iban = normalize_iban(iban).upper()
        try:
            validate_iban(normalized_iban)
        except ValidationError:
            chatter_msg.append(
                self.env._(
                    "IBAN <b>%(iban)s</b> is not valid, so it has been ignored.",
                    iban=normalized_iban,
                )
            )
            return False
        return super()._match_partner_bank(
            partner,
            normalized_iban,
            bic,
            chatter_msg,
            create_if_not_found=create_if_not_found,
        )
