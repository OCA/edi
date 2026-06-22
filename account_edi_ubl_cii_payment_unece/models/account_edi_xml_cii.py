# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class AccountEdiXmlCII(models.AbstractModel):
    _inherit = "account.edi.xml.cii"

    def _export_invoice_vals(self, invoice):
        template_values = super()._export_invoice_vals(invoice)
        payment_method_line = invoice.preferred_payment_method_line_id
        payment_method = payment_method_line.payment_method_id
        if payment_method.unece_id:
            # Integrate UNECE payment means
            template_values["payment_means_code"] = payment_method.unece_id.code
        return template_values

    def _import_fill_invoice(self, invoice, tree, qty_factor):
        res = super()._import_fill_invoice(invoice, tree, qty_factor)
        invoice_values = self._extract_invoice_unece_payment_mean(invoice, tree)
        if invoice_values:
            invoice.write(invoice_values)
        return res

    def _extract_invoice_unece_payment_mean(self, invoice, tree):
        payment_mean_code = None
        for node in tree.findall(
            ".//{*}SpecifiedTradeSettlementPaymentMeans/{*}TypeCode"
        ):
            if payment_mean_code := node.text:
                break
        if not payment_mean_code:
            return {}
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
        return {"preferred_payment_method_line_id": payment_method_line.id}
