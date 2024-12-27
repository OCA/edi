# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# In v17, the method _is_invoice_report(report_ref) of ir.actions.report
# was returning True for the 2 invoices reports.
# In v18, a new boolean field is_invoice_report was added to ir.actions.report
# but, surprisingly, it is set to True for report XMLID account.account_invoices
# but left to False for report XMLID account.account_invoices_without_payment
# (which is the report that users can access via the print menu).
# This post_install script fixes this.
def update_invoice_report_config(env):
    env.ref("account.account_invoices_without_payment").write(
        {"is_invoice_report": True}
    )
