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


{
    'name': 'OVH Supplier Invoice',
    'version': '0.3',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Get OVH Invoice via the API',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': ['account', 'base_vat_sanitized'],
    'external_dependencies': {'python': ['requests', 'SOAPpy']},
    'data': [
        'ovh_account_view.xml',
        'security/ir.model.access.csv',
        'security/ovh_security.xml',
        'wizard/ovh_invoice_get_view.xml',
    ],
    'demo': ['ovh_demo.xml'],
    'installable': True,
}
