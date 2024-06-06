# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "voxel.mixin"]

    voxel_enabled = fields.Boolean(
        compute="_compute_voxel_enabled",
        search="_search_voxel_enabled",
    )
    voxel_job_ids = fields.Many2many(
        comodel_name="queue.job",
        relation="account_invoice_voxel_job_rel",
        column1="invoice_id",
        column2="voxel_job_id",
        string="Jobs",
        copy=False,
    )

    def get_voxel_login(self, company=None):
        """This method overwrites the one defined in voxel.mixin to provide
        the login for this specific model (account.invoice)
        """
        return (company or self.company_id).voxel_invoice_login_id

    def _compute_voxel_enabled(self):
        for record in self:
            record.voxel_enabled = (
                record.company_id.voxel_enabled and record.partner_id.voxel_enabled
            )

    def _search_voxel_enabled(self, operator, value):
        if (operator == "=" and value) or (operator == "!=" and not value):
            domain = [
                ("company_id.voxel_enabled", "=", True),
                ("partner_id.voxel_enabled", "=", True),
            ]
        else:
            domain = [
                "|",
                ("company_id.voxel_enabled", "=", False),
                ("partner_id.voxel_enabled", "=", False),
            ]
        return [("id", "in", self.search(domain).ids)]

    def _post(self, soft=True):
        """Send to Voxel when posting."""
        res = super()._post(soft=soft)
        self.action_send_to_voxel()
        return res

    def button_draft(self):
        res = super().button_draft()
        self._cancel_voxel_jobs()
        return res

    def action_send_to_voxel(self):
        invoices = self.filtered(
            lambda inv: inv.is_sale_document() and inv.voxel_enabled
        )
        if invoices:
            invoices.enqueue_voxel_report(
                "edi_voxel_account_invoice_oca.report_voxel_invoice"
            )

    def get_document_type(self):
        """Document type name to be used in the name of the Voxel report"""
        return "Factura"
