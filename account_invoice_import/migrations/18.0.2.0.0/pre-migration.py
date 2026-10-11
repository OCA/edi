# Copyright 2026 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_column_renames = {
    "res_partner": [("invoice_import_single_line", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module set state='uninstalled' WHERE
        name in (
           'account_invoice_import_ubl',
           'account_invoice_import_facturx',
           'l10n_fr_account_invoice_import_facturx')
        """,
    )
