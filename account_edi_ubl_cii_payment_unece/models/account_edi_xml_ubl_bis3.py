# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class AccountEdiXmlUBLBIS3(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_bis3"

    def _ubl_add_payment_means_nodes(self, vals):
        super()._ubl_add_payment_means_nodes(vals)
        nodes = vals["document_node"]["cac:PaymentMeans"]
        invoice = vals.get("invoice")
        if not invoice:
            return
        payment_method_line = invoice.preferred_payment_method_line_id
        payment_method = payment_method_line.payment_method_id
        if payment_method.unece_id:
            # Integrate UNECE payment means
            for node in nodes:
                node["cbc:PaymentMeansCode"] = {
                    "_text": payment_method.unece_id.code,
                    "name": payment_method.unece_id.name,
                }
