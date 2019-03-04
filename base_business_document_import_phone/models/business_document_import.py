# Copyright 2015-2019 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
import logging
logger = logging.getLogger(__name__)
try:
    import phonenumbers
except ImportError:
    logger.debug('Cannot import phonenumbers')


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _hook_match_partner(
            self, partner_dict, chatter_msg, domain, partner_type_label):
        rpo = self.env['res.partner']
        # 'domain' already contains the company_id criteria
        if partner_dict.get('country_code') and partner_dict.get('phone'):
            phone_num_e164 = False
            try:
                phone_num = phonenumbers.parse(
                    partner_dict['phone'],
                    partner_dict['country_code'].upper())
                phone_num_e164 = phonenumbers.format_number(
                    phone_num, phonenumbers.PhoneNumberFormat.E164)
            except:
                pass
            logger.debug(
                '_hook_match_partner phone_num_e164: %s', phone_num_e164)
            if phone_num_e164:
                partners = rpo.search(domain + [
                    '|',
                    ('phone', '=', phone_num_e164),
                    ('mobile', '=', phone_num_e164)])
                if partners:
                    return partners[0]
        return super(BusinessDocumentImport, self)._hook_match_partner(
            partner_dict, chatter_msg, domain, partner_type_label)
