# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError


class BaseUbl(models.AbstractModel):
    _inherit = "base.ubl"

    @api.model
    def _ubl_add_payment_means(
        self,
        partner_bank,
        payment_mode,
        date_due,
        parent_node,
        ns,
        payment_identifier=None,
        version="2.1",
    ):
        res = super()._ubl_add_payment_means(
            partner_bank,
            payment_mode,
            date_due,
            parent_node,
            ns,
            payment_identifier=payment_identifier,
            version=version,
        )
        self._ubl_add_payment_mandate(parent_node, ns)
        return res

    @api.model
    def _ubl_add_payment_mandate(self, parent_node, ns):
        payment_means_nodes = parent_node.findall(ns["cac"] + "PaymentMeans")
        if not payment_means_nodes:
            # nothing to do if the payment block was not generated
            return

        payment_means = payment_means_nodes[-1]
        payment_means_code = payment_means.find(ns["cbc"] + "PaymentMeansCode")
        if payment_means_code is None or payment_means_code.text not in ("49", "59"):
            # peppol only requires PaymentMandate for direct debit means
            return

        if not self.mandate_id:
            # direct debit invoices must carry a mandate reference
            raise UserError(
                _(
                    "A mandate reference must be provided for direct debit "
                    "payment means code %(code)s.",
                    code=payment_means_code.text,
                )
            )

        payer_bank = self.mandate_id.partner_bank_id
        payer_iban = payer_bank.sanitized_acc_number
        if not payer_iban:
            raise UserError(
                _("The direct debit mandate must have a payer bank account.")
            )

        payment_mandate = etree.SubElement(
            payment_means,
            ns["cac"] + "PaymentMandate",
        )
        mandate_id = etree.SubElement(payment_mandate, ns["cbc"] + "ID")
        mandate_id.text = self.mandate_id.unique_mandate_reference

        payer_financial_account = etree.SubElement(
            payment_mandate,
            ns["cac"] + "PayerFinancialAccount",
        )
        payer_financial_account_id = etree.SubElement(
            payer_financial_account,
            ns["cbc"] + "ID",
        )
        payer_financial_account_id.text = payer_iban
