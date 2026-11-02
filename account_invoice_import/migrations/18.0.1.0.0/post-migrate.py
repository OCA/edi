# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade, openupgrade_180


@openupgrade.migrate()
def migrate(env, version):
    openupgrade_180.convert_company_dependent(
        env, "res.partner", "invoice_import_product_id"
    )
    openupgrade_180.convert_company_dependent(
        env, "res.partner", "invoice_import_account_id"
    )
    openupgrade_180.convert_company_dependent(
        env, "res.partner", "invoice_import_single_line"
    )
    openupgrade_180.convert_company_dependent(
        env, "res.partner", "invoice_import_label"
    )
    openupgrade_180.convert_company_dependent(
        env, "res.partner", "invoice_import_journal_id"
    )
