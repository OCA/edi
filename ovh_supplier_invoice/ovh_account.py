# -*- encoding: utf-8 -*-
##############################################################################
#
#    OVH Supplier Invoice module for Odoo
#    Copyright (C) 2015 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class OvhAccount(models.Model):
    _name = 'ovh.account'
    _description = 'OVH Account Information'
    _rec_name = 'login'

    login = fields.Char(string='OVH NIC', required=True)
    password = fields.Char(string='OVH Password')
    active = fields.Boolean(default=True)
    invoice_line_method = fields.Selection([
        ('product', 'With Product'),
        ('no_product', 'Without Product'),
        ], string='Method for Invoice Line', required=True,
        default='no_product')
    company_id = fields.Many2one(
        'res.company', string='Company',
        ondelete='cascade', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'ovh.account'))
    account_id = fields.Many2one(
        'account.account', string='Expense Account',
        domain=[('type', 'not in', ('view', 'closed'))])
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        domain=[('type', '!=', 'view')])
