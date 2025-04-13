# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from openupgradelib import openupgrade

from odoo import Command


@openupgrade.migrate()
def migrate(env, version):
    company2partner = defaultdict(list)
    config2tax = defaultdict(list)
    openupgrade.logged_query(
        env.cr,
        """
        SELECT * FROM account_invoice_import_config_account_tax_rel
        WHERE account_invoice_import_config_id is not null
        AND account_tax_id is not null
        """,
    )
    for entry in env.cr.dictfetchall():
        config2tax[entry["account_invoice_import_config_id"]].append(
            entry["account_tax_id"]
        )
    config_table = openupgrade.get_legacy_name("account_invoice_import_config")
    openupgrade.logged_query(
        env.cr,
        f"SELECT * FROM {config_table} WHERE company_id is not null "
        f"AND invoice_line_method != 'nline_auto_product' AND partner_id is not null "
        f"AND active is true ORDER BY sequence, id",
    )

    for config in env.cr.dictfetchall():
        partner_id = config["partner_id"]
        company_id = config["company_id"]
        if partner_id in company2partner.get(company_id, []):
            continue
        company2partner[company_id].append(partner_id)
        partner = env["res.partner"].browse(partner_id)
        vals = {}
        if config["invoice_line_method"].startswith("1line_"):
            vals["invoice_import_single_line"] = True
        if (
            config["invoice_line_method"]
            in ("1line_static_product", "nline_static_product")
            and config["static_product_id"]
        ):
            vals["invoice_import_product_id"] = config["static_product_id"]
        if (
            config["invoice_line_method"] in ("1line_no_product", "nline_no_product")
            and config["account_id"]
        ):
            vals["invoice_import_account_id"] = config["account_id"]
            if config2tax.get(config["id"], []):
                vals["invoice_import_tax_ids"] = []
                for tax_id in config2tax[config["id"]]:
                    vals["invoice_import_tax_ids"].append(Command.link(tax_id))
        if config["label"]:
            vals["invoice_import_label"] = config["label"]
        if config["journal_id"]:
            vals["invoice_import_journal_id"] = config["journal_id"]
        if vals:
            partner.with_company(company_id).write(vals)
