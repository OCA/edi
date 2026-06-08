# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUbl_20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _import_fill_invoice_form(self, journal, tree, invoice, qty_factor):
        res = super()._import_fill_invoice_form(journal, tree, invoice, qty_factor)
        if invoice.invoice_origin:
            po = self.env["purchase.order"].search(
                [
                    "|",
                    ("name", "=", invoice.invoice_origin),
                    ("partner_ref", "=", invoice.invoice_origin),
                    ("state", "in", ("purchase", "done")),
                ],
                limit=1,
            )
            if po:
                invoice.partner_id = po.partner_id
        return res
