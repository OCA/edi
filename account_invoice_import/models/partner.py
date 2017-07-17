# -*- coding: utf-8 -*-
# © 2015-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2017-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_import_id = fields.Many2one(
        'account.invoice.import.config',
        string='Invoice Import Configuration',
        company_dependent=True)
