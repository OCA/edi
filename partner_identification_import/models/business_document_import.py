# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(self, partner_dict, chatter_msg, domain, order):
        # Loop on all the partner_dict["id_number"] and search for a partner
        # having one.  If the schemeID matches an existing Id Number Category,
        # then a match is required.
        schemeIDs = [
            e["schemeID"] for e in partner_dict.get("id_number", []) if e["schemeID"]
        ]
        if schemeIDs:
            schemes = self.env["res.partner.id_category"].search(
                [("code", "in", schemeIDs)]
            )
            unmatched = []
            for ident in partner_dict.get("id_number", []):
                if ident.get("schemeID") not in schemes.mapped("code"):
                    continue
                categ = schemes.filtered(lambda s: s.code == ident["schemeID"])
                id_number = self.env["res.partner.id_number"].search(
                    [
                        ("category_id", "in", categ.ids),
                        ("name", "=", ident["value"]),
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
                    contact = self._match_partner_contact(
                        partner_dict, chatter_msg, domain, order
                    )
                    if contact:
                        return contact
                    return id_number.partner_id
                unmatched.append(
                    _("ID Number: {}\nID Number Category: {}\n\n").format(
                        ident["value"], ident["schemeID"]
                    )
                )
            if unmatched:
                raise self.user_error_wrap(
                    "_hook_match_partner",
                    partner_dict,
                    _(
                        "Odoo couldn't find a partner corresponding to the "
                        "following information extracted from the business document:\n"
                        "{}"
                    )
                    .format("or\n")
                    .join(unmatched),
                )
        return super()._hook_match_partner(partner_dict, chatter_msg, domain, order)
