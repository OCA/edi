# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

logger = logging.getLogger(__name__)
try:
    import phonenumbers
except ImportError:
    logger.debug("Cannot import phonenumbers")


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(self, partner_dict, chatter_msg, domain, order):
        rpo = self.env["res.partner"]
        # 'domain' already contains the company_id criteria
        if partner_dict.get("country_code") and partner_dict.get("phone"):
            phone_num_intl = False
            country_code = partner_dict["country_code"].upper()
            try:
                phone_num = phonenumbers.parse(partner_dict["phone"], country_code)
                phone_num_intl = phonenumbers.format_number(
                    phone_num, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                logger.debug("_hook_match_partner phone_num_intl: %s", phone_num_intl)
            except Exception as e:
                logger.debug(
                    "Could not reformat phone number '%s' with country code '%s'. "
                    "Error: %s'",
                    partner_dict["phone"],
                    country_code,
                    e,
                )
            if phone_num_intl:
                partner = rpo.search(
                    domain
                    + [
                        "|",
                        ("phone", "=", phone_num_intl),
                        ("mobile", "=", phone_num_intl),
                    ],
                    limit=1,
                    order=order,
                )
                if partner:
                    return partner
        return super()._hook_match_partner(partner_dict, chatter_msg, domain, order)
