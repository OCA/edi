# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import requests

import odoo
from odoo import _, fields, models
from odoo.exceptions import UserError, except_orm


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_exported = fields.Boolean(copy=False)
    # Usefull when the distant system does not validate the export synchronously
    invoice_export_confirmed = fields.Boolean(copy=False)
    send_through_http = fields.Boolean(related="transmit_method_id.send_through_http")

    def export_invoice(self):
        for invoice in self:
            description = "{} - Export ebill".format(invoice.transmit_method_id.name)
            invoice.with_delay(description=description)._job_export_invoice()

    def _job_export_invoice(self):
        """Export ebill to external server and update the chatter."""
        self.ensure_one()
        if self.invoice_exported and self.invoice_export_confirmed:
            return _("Nothing done, invoice has already been exported before.")
        try:
            res = self._export_invoice()
        except Exception as e:
            values = {
                "job_id": self.env.context.get("job_uuid"),
                "error_detail": "",
                "error_type": type(e).__name__,
                "transmit_method_name": self.transmit_method_id.name,
            }
            if isinstance(e, except_orm):
                values["error_detail"] = e.name
            with odoo.api.Environment.manage():
                with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                    # Create a new environment with new cursor database
                    new_env = odoo.api.Environment(
                        new_cr, self.env.uid, self.env.context
                    )
                    # The chatter of the invoice need to be updated, when the job fails
                    self.with_env(new_env).log_error_sending_invoice(values)
            raise
        self.invoice_send = True
        self.log_success_sending_invoice()
        return res

    def _export_invoice(self):
        """Export electronic invoice to external service."""
        if not self.transmit_method_id.send_through_http:
            raise UserError(_("Transmit method is not configured to send through HTTP"))
        file_data = self._get_file_for_transmission_method()
        headers = self.transmit_method_id.get_transmission_http_header()
        res = requests.post(
            self.transmit_method_id.destination_url,
            headers=headers,
            files=file_data,
        )
        if res.status_code != 200:
            raise UserError(
                _(
                    "HTTP error {} sending invoice to {}".format(
                        res.status_code, self.transmit_method_id.name
                    )
                )
            )
        self.invoice_exported = self.invoice_export_confirmed = True
        return res.text

    def _get_file_for_transmission_method(self):
        """Return the file description to send.

        Use the format expected by the request library
        By default returns the PDF report.
        """
        r = self.env["ir.actions.report"]._get_report_from_name(
            "account.report_invoice"
        )
        pdf, _ = r._render([self.id])
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
            message = self.env.ref(
                "account_invoice_export.exception_sending_invoice"
            )._render(values=values)
            activity = self.activity_schedule(
                activity_type, summary="Job error sending invoice", note=message
            )
        error_log = values.get("error_detail")
        if not error_log:
            error_log = _("An error of type {} occured.").format(
                values.get("error_type")
            )
        activity.note += "<div class='mt16'><p>{}</p></div>".format(error_log)

    def log_success_sending_invoice(self):
        """Log success sending invoice and clear existing exception, if any."""
        self.activity_feedback(
            ["account_invoice_export.mail_activity_transmit_warning"],
            feedback="It worked on a later try",
        )
        self.message_post(
            body=_("Invoice successfuly sent to {}").format(
                self.transmit_method_id.name
            )
        )
