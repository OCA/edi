# Copyright 2026 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


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
        pay_means = super()._ubl_add_payment_means(
            partner_bank,
            payment_mode,
            date_due,
            parent_node,
            ns,
            payment_identifier=payment_identifier,
            version=version,
        )
        if (
            payment_mode.payment_method_id.unece_code in ["49", "59"]
            and self.mandate_id
        ):
            # Direct Debit requires mandate
            pay_means_mandate = etree.SubElement(
                pay_means, ns["cac"] + "PaymentMandate"
            )
            etree.SubElement(
                pay_means_mandate, ns["cbc"] + "ID"
            ).text = self.mandate_id.unique_mandate_reference
            payer = etree.SubElement(
                pay_means_mandate, ns["cac"] + "PayerFinancialAccount"
            )
            etree.SubElement(
                payer, ns["cbc"] + "ID"
            ).text = self.mandate_id.partner_bank_id.acc_number
        return pay_means
