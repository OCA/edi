# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(self, partner_dict, chatter_msg, domain, order):
        if partner_dict.get("id_number") and partner_dict.get("id_schemeID"):
            categ = self.env["res.partner.id_category"].search(
                [("code", "=", partner_dict.get("id_schemeID"))]
            )
            if categ:
                id_number = self.env["res.partner.id_number"].search(
                    [
                        ("category_id", "=", categ.id),
                        ("name", "=", partner_dict["id_number"]),
                        ("status", "!=", "close"),
                    ],
                    limit=1,
                )
                if id_number:
                    partner = id_number.partner_id
                    # Search for a contact of this partner
                    domain = [
                        ("parent_id", "=", partner.id),
                        ("is_company", "=", False),
                    ]
                    contact = self._match_partner_contact(partner_dict, domain, order)
                    if contact:
                        return contact
                    return id_number.partner_id
                raise self.user_error_wrap(
                    _(
                        "Odoo couldn't find a partner corresponding to the "
                        "following information extracted from the business document:\n"
                        "ID Number: %s\n"
                        "ID Number Category: %s\n"
                    )
                    % (partner_dict["id_number"], partner_dict["id_schemeID"])
                )
        return super()._hook_match_partner(partner_dict, chatter_msg, domain, order)
