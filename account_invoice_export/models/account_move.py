# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import requests

import odoo
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_exported = fields.Boolean(copy=False)
    # Usefull when the distant system does not validate the export synchronously
    invoice_export_confirmed = fields.Boolean(copy=False)
    send_through_http = fields.Boolean(related="transmit_method_id.send_through_http")

    def _validate_exportable_invoices(self):
        """Check if invoices are valid for export and raise ValidationError if not."""

        def format_invoice_list(invoices):
            return "\n- " + "\n- ".join(
                self.env._("%(name)s (Invoice Record ID: %(id)s)")
                % {"name": inv.name or self.env._("Draft"), "id": inv.id}
                for inv in invoices
            )

        errors = []

        # Check for invoices not in 'posted' state
        not_posted_invoices = self.filtered(lambda inv: inv.state != "posted")
        if not_posted_invoices:
            errors.append(
                self.env._("Invoices not in 'Posted' state: %s")
                % format_invoice_list(not_posted_invoices)
            )

        # Check for unsupported invoice types
        unsupported_type_invoices = self.filtered(
            lambda inv: inv.move_type not in ("out_invoice", "out_refund")
        )
        if unsupported_type_invoices:
            errors.append(
                self.env._(
                    "Invoices with unsupported type "
                    "(only Customer Invoice or Refund are allowed): %s"
                )
                % format_invoice_list(unsupported_type_invoices)
            )

        if errors:
            raise ValidationError("\n\n".join(errors))

    def export_invoice(self):
        # Validate invoices to ensure they are exportable before proceeding
        self._validate_exportable_invoices()
        resend_invoice = self.env.context.get("resend_ebill", False)
        for invoice in self:
            # Added condition to resend ebill through server action
            # if requested or already exported
            invoice._job_export_invoice(resend_invoice or invoice.invoice_exported)

    def _job_export_invoice(self, resend_invoice=False):
        """Export ebill to external server and update the chatter."""
        self.ensure_one()
        if (
            not resend_invoice
            and self.invoice_exported
            and self.invoice_export_confirmed
        ):
            return self.env._("Nothing done, invoice has already been exported before.")
        try:
            res = self._export_invoice()
        except Exception as e:
            values = {
                "job_id": self.env.context.get("job_uuid"),
                "error_detail": "",
                "error_type": type(e).__name__,
                "transmit_method_name": self.transmit_method_id.name,
            }
            with Registry(self.env.cr.dbname).cursor() as new_cr:
                # Create a new environment with new cursor database
                new_env = odoo.api.Environment(new_cr, self.env.uid, self.env.context)
                # The chatter of the invoice need to be updated, when the job fails
                self.with_env(new_env).log_error_sending_invoice(values)
            raise
        self.log_success_sending_invoice()
        return res

    def _export_invoice(self):
        """Export electronic invoice to external service."""
        if not self.transmit_method_id.send_through_http:
            raise UserError(
                self.env._("Transmit method is not configured to send through HTTP")
            )
        url = self.transmit_method_id.get_transmission_url()
        # If no URL is configured, raise an error
        if not url:
            raise UserError(
                self.env._("No valid URL configured on transmit method '%s'.")
                % (self.transmit_method_id.name or "N/A")
            )
        file_data = self._get_file_for_transmission_method()
        headers = self.transmit_method_id.get_transmission_http_header()
        # TODO: Should be configurable as a parameter
        res = requests.post(url, headers=headers, files=file_data, timeout=10)
        if res.status_code != 200:
            raise UserError(
                self.env._("HTTP error %s sending invoice to %s")
                % (res.status_code, self.transmit_method_id.name)
            )
        self.invoice_exported = self.invoice_export_confirmed = True
        return res.text

    def _get_file_for_transmission_method(self):
        """Return the file description to send.

        Use the format expected by the request library
        By default returns the PDF report.
        """
        report = "account.report_invoice"
        pdf, _ = self.env["ir.actions.report"]._render(report, [self.id])
        filename = self._get_report_base_filename().replace("/", "_") + ".pdf"
        return {"file": (filename, pdf, "application/pdf")}

    def log_error_sending_invoice(self, values):
        """Log an exception in invoice's chatter when sending fails.

        If an exception already exists it is update otherwise a new one
        is created.
        """
        activity_type = "account_invoice_export.mail_activity_transmit_warning"
        activity = self.activity_reschedule(
            [activity_type], date_deadline=fields.Date.today()
        )
        if not activity:
            template = "account_invoice_export.exception_sending_invoice"
            message = self.env["ir.ui.view"]._render_template(template, values=values)
            activity = self.activity_schedule(
                activity_type, summary="Job error sending invoice", note=message
            )
        error_log = values.get("error_detail")
        if not error_log:
            error_log = self.env._("An error of type {} occured.").format(
                values.get("error_type")
            )
        activity.note += f"<div class='mt16'><p>{error_log}</p></div>"

    def log_success_sending_invoice(self):
        """Log success sending invoice and clear existing exception, if any."""
        self.activity_feedback(
            ["account_invoice_export.mail_activity_transmit_warning"],
            feedback="It worked on a later try",
        )
        self.message_post(
            body=self.env._("Invoice successfuly sent to {}").format(
                self.transmit_method_id.name
            )
        )
