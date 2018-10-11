# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Invoice Import UBL module for Odoo
#    Copyright (C) 2016 Akretion (http://www.akretion.com)
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
    'name': 'Account Invoice Import UBL',
    'version': '8.0.0.1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import UBL XML supplier invoices/refunds',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    # TODO : rename module base_zugferd
    # because it seems payment means code and some tax codes
    # are common between zugferd/CII and UBL !
    'depends': ['account_invoice_import', 'base_vat', 'base_zugferd'],
    'data': [],
    'demo': ['demo/demo_data.xml'],
    'test': ['test/ubl.yml'],
    'installable': True,
}
