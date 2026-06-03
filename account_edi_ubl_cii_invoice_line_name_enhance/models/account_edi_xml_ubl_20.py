# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _import_fill_invoice_line_form(
        self, journal, tree, invoice, invoice_line, qty_factor
    ):
        res = super()._import_fill_invoice_line_form(
            journal, tree, invoice, invoice_line, qty_factor
        )
        description = None
        product_name = None
        description_node = tree.find("./{*}Item/{*}Description")
        name_node = tree.find("./{*}Item/{*}Name")
        if description_node is not None:
            description = description_node.text
        if name_node is not None:
            product_name = name_node.text
        if product_name and description and product_name not in description:
            invoice_line.name = f"{product_name}\n{description}"
        return res
