# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# Copyright 2026 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class AccountEdiXmlCII(models.AbstractModel):
    _inherit = "account.edi.xml.cii"

    def _export_invoice_get_payment_means_code(self, invoice):
        """Returns UNECE payment means code if set on the invoice"""
        payment_method_line = invoice.preferred_payment_method_line_id
        payment_method = payment_method_line.payment_method_id
        if not payment_method.unece_id:
            return
        return payment_method.unece_id.code

    def _export_invoice_vals(self, invoice):
        template_values = super()._export_invoice_vals(invoice)
        payment_means_code = self._export_invoice_get_payment_means_code(invoice)
        if payment_means_code:
            template_values["payment_means_code"] = payment_means_code
        return template_values

    def _cii_get_applicable_header_trade_settlement_node(self, vals):
        res = super()._cii_get_applicable_header_trade_settlement_node(vals)
        invoice = vals.get("invoice")
        if not invoice:
            return res
        payment_means_code = self._export_invoice_get_payment_means_code(invoice)
        if not payment_means_code:
            return res
        type_code = res.get("ram:SpecifiedTradeSettlementPaymentMeans", {}).get(
            "ram:TypeCode", {}
        )
        if type_code:
            type_code["_text"] = payment_means_code
        return res

    def _import_cii_invoice_add_payment_reference(self, collected_values):
        res = super()._import_cii_invoice_add_payment_reference(collected_values)
        self._import_cii_invoice_add_payment_means(collected_values)
        return res

    def _import_cii_invoice_add_payment_means(self, collected_values):
        payment_mean_code = None
        tree = collected_values["tree"]
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
        collected_values["to_write"]["preferred_payment_method_line_id"] = (
            payment_method_line.id
        )
