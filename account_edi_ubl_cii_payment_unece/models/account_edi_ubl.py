# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class AccountEdiUBL(models.AbstractModel):
    _inherit = "account.edi.ubl"

    def _import_ubl_invoice_add_payment_reference(self, collected_values):
        # NOTE: we override this method to access `collected_values`. It could
        # have been any method called in '<account.edi.ubl>._ubl_import_invoice()'.
        res = super()._import_ubl_invoice_add_payment_reference(collected_values)
        self._import_ubl_invoice_add_unece_payment_mean(collected_values)
        return res

    def _import_ubl_invoice_add_unece_payment_mean(self, collected_values):
        tree = collected_values["tree"]
        payment_mean_code = None
        for node in tree.findall("./{*}PaymentMeans/{*}PaymentMeansCode"):
            if note := node.text:
                payment_mean_code = note
                break
        if not payment_mean_code:
            return
        # Look for a matching payment method line
        payment_method_line = self.env["account.payment.method.line"].search(
            [
                ("journal_id.type", "in", ("cash", "bank", "credit")),
                ("payment_type", "=", "outbound"),
                ("payment_method_id.unece_code", "=", payment_mean_code),
            ],
            limit=1,
        )
        if not payment_method_line:
            return
        collected_values["to_write"]["preferred_payment_method_line_id"] = (
            payment_method_line.id
        )
