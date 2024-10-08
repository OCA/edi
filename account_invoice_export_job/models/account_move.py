# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import models

from odoo.addons.queue_job.job import identity_exact


class AccountMove(models.Model):
    _inherit = "account.move"

    def _job_export_invoice_job_options(self, resend_invoice=False):
        description = f"Export eBill to {self.transmit_method_id.name}"
        return {
            "description": description,
            "identity_key": identity_exact,
        }

    def export_invoice(self):
        with_context = self.with_context(auto_delay_export_invoice=True)
        return super(AccountMove, with_context).export_invoice()

    def _register_hook(self):
        """Patch export invoice to be automatically delayed as job."""
        mapping = {"_job_export_invoice": "auto_delay_export_invoice"}
        for method_name, context_key in mapping.items():
            self._patch_method(
                method_name,
                self._patch_job_auto_delay(method_name, context_key=context_key),
            )
        return super()._register_hook()
