# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        This is only necessary when tests are enabled.
        It forces the creation of pdf instead of html."""
        # Even if not expected, we might get an ID.
        # Eg https://github.com/odoo/odoo/blob/10378872eddd6037f479fa8cbb3ed65d5e4b52c6
        # /addons/account/models/account_bank_statement.py#L440
        if (
            isinstance(res_ids, int)
            or len(res_ids or []) == 1
            and not self.env.context.get("no_embedded_ubl_xml")
        ):
            if len(self) == 1 and self.is_ubl_xml_to_embed_in_purchase_order():
                self = self.with_context(force_report_rendering=True)
        res = super()._render_qweb_pdf(report_ref, res_ids, data)
        if res_ids and len(res_ids) == 1:
            if self.is_ubl_xml_to_embed_in_purchase_order():
                purchase_order = self.env["purchase.order"].browse(res_ids)
                res = purchase_order.embed_ubl_xml_in_pdf(res)
        return res

    def is_ubl_xml_to_embed_in_purchase_order(self):
        return (
            self.model == "purchase.order"
            and not self.env.context.get("no_embedded_ubl_xml")
            and self.report_name in self._get_purchase_order_ubl_reports()
        )

    def _get_purchase_order_ubl_reports(self):
        return ["purchase.report_purchaseorder", "purchase.report_purchasequotation"]
