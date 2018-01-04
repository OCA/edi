# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import From a Directory',
    'description': """
        Allows to automatically load xml and/or PDF file from a directory on
        the Odoo server
        """,
    'version': '10.0.1.0.0',
    'depends': [
        'account_invoice_import',
        'base_technical_user',
        'queue_job'
    ],
    'author': 'ACSONE SA/NV, Odoo Community Association (OCA)',
    'website':
        'https://github.com/OCA/edi/tree/10.0/'
        'account_invoice_import_directory',
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_import_directory.xml',
    ],
    'installable': True,
}
