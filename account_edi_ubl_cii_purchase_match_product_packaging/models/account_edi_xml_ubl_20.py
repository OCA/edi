# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUbl_20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _import_fill_invoice_line_packaging(self, invoice_line):
        res = super()._import_fill_invoice_line_packaging(invoice_line)
        # force recomputation of the quantity
        # this is needed because after a second reconciliation with a purchase line,
        # the packaging may remain the same while the underlying quantity changes
        # without this explicit call, the computed quantity may become inconsistent
        invoice_line._compute_quantity()
        return res
