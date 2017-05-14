# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2017-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import models, api, _


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_incoterm(self, incoterm_dict, chatter_msg):
        sio = self.env['stock.incoterms']
        if not incoterm_dict:
            return False
        if incoterm_dict.get('recordset'):
            return incoterm_dict['recordset']
        if incoterm_dict.get('id'):
            return sio.browse(incoterm_dict['id'])
        if incoterm_dict.get('code'):
            incoterms = sio.search([
                '|',
                ('name', '=ilike', incoterm_dict['code']),
                ('code', '=ilike', incoterm_dict['code'])])
            if incoterms:
                return incoterms[0]
            else:
                chatter_msg.append(_(
                    "Could not find any Incoterm in Odoo corresponding "
                    "to '%s'") % incoterm_dict['code'])
        return False
