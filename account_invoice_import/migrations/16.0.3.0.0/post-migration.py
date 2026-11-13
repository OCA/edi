# Copyright 2026 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    invoice_import_shrink_lines_field = env['ir.model.fields'].search([
        ('ttype', '=', 'selection'),
        ('model', '=', 'res.partner'),
        ('name', '=', 'invoice_import_shrink_lines'),
        ], limit=1)
    if invoice_import_shrink_lines_field:
        invoice_import_shrink_lines_field_id = invoice_import_shrink_lines_field.id
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE ir_property
            SET
            name='invoice_import_shrink_lines',
            type='selection',
            value_text='per_vat_rate',
            fields_id=%s
            WHERE
            name='invoice_import_single_line'
            AND type='boolean'
            AND res_id like 'res.partner,%%'
            """, (invoice_import_shrink_lines_field_id, )
        )
