# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(
        self, partner_dict, chatter_msg, domain, partner_type_label
    ):
        if partner_dict.get("id_number") and partner_dict.get("id_schemeID"):
            categ = self.env["res.partner.id_category"].search(
                [("code", "=", partner_dict.get("id_schemeID"))]
            )
            if categ:
                # partner_identification_gln is installed
                id_number = self.env["res.partner.id_number"].search(
                    [
                        ("category_id", "=", categ.id),
                        ("name", "=", partner_dict["id_number"]),
                    ],
                    limit=1,
                )
                if id_number:
                    return id_number.partner_id
        return super()._hook_match_partner(
            partner_dict, chatter_msg, domain, partner_type_label
        )
