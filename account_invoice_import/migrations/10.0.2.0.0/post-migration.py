# -*- coding: utf-8 -*-
# © 2018 Akretion (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        aiico = env['account.invoice.import.config']
        ipo = env['ir.property']

        for config in aiico.search([]):
            value_ref = 'account.invoice.import.config,%d' % config.id
            props = ipo.search([
                ('name', '=', 'invoice_import_id'),
                ('type', '=', 'many2one'),
                ('value_reference', '=', value_ref),
                ('company_id', '=', config.company_id.id),
                ('res_id', '=like', 'res.partner,%'),
                ])
            if props and props[0].res_id:
                res_id_split = props[0].res_id.split(',')
                try:
                    partner_id = int(res_id_split[1])
                except Exception:
                    continue
                config.partner_id = partner_id
                props.unlink()
