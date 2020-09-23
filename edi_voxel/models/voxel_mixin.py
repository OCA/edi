# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from urllib.parse import urljoin

import requests
from lxml import etree

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug("Can not `import queue_job`.")
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial

    job = empty_decorator_factory


class VoxelMixin(models.AbstractModel):
    _name = "voxel.mixin"
    _description = "Voxel mixin"

    voxel_state = fields.Selection(
        selection=[
            ("not_sent", "Not sent"),
            ("sent", "Sent not verified"),
            ("sent_errors", "Sending error"),
            ("accepted", "Sent and accepted"),
            ("processing_error", "Processing error"),
            ("cancelled", "Cancelled"),
        ],
        string="Voxel send state",
        default="not_sent",
        readonly=True,
        copy=False,
        help="Indicates the status of sending report to Voxel",
    )
    voxel_xml_report = fields.Text(string="XML Report", readonly=True)
    voxel_filename = fields.Char(string="Voxel filename", readonly=True)
    processing_error = fields.Text(string="Processing error", readonly=True)

    # Export methods
    # --------------
    def enqueue_voxel_report(self, report_name):
        eta = self.company_id._get_voxel_report_eta()
        queue_obj = self.env["queue.job"].sudo()
        for record in self.sudo():
            # Look first if there's a failing job. If so, retry that one
            failing_job = record.voxel_job_ids.filtered(lambda x: x.state == "failed")[
                :1
            ]
            if failing_job:
                failing_job.voxel_requeue_sudo()
                continue
            # If not, create a new one
            new_delay = (
                record.with_context(company_id=self.company_id.id)
                .with_delay(eta=eta)
                ._get_and_send_voxel_report(report_name)
            )

            job = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
            record.voxel_job_ids |= job

    @job(default_channel="root.voxel_export")
    def _get_and_send_voxel_report(self, report_name):
        self.ensure_one()
        report = self.env.ref(report_name)
        report_xml = report.render_qweb_xml(self.ids, {})[0]
        # Remove blank spaces
        tree = etree.fromstring(report_xml, etree.XMLParser(remove_blank_text=True))
        clean_report_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        file_name = self._get_voxel_filename()
        self._send_voxel_report("Outbox", file_name, clean_report_xml)
        self.write(
            {
                "voxel_state": "sent",
                "voxel_filename": file_name,
                "voxel_xml_report": report_xml,
            }
        )

    # export error detection methods
    # ------------------------------
    def _cron_update_voxel_export_status(self):
        for company in self.env["res.company"].search([]):
            if company.voxel_enabled and self.get_voxel_login(company):
                self._update_voxel_export_status(company)

    def _update_voxel_export_status(self, company):
        sent_docs = self.search([("voxel_state", "=", "sent")])
        if not sent_docs:
            return
        queue_obj = self.env["queue.job"].sudo()
        # Determine processed documents
        filenames = self._list_voxel_document_filenames("Outbox", company)
        processed = sent_docs.filtered(lambda r: r.voxel_filename not in filenames)
        # Determine documents with errors
        filenames = self._list_voxel_document_filenames("Error", company)
        with_errors = processed.filtered(lambda r: r.voxel_filename in filenames)
        doc_dict = {}
        for doc in with_errors:
            if doc.voxel_filename:
                doc_dict[doc.voxel_filename] = doc
        for filename in filenames:
            if filename.endswith(".log"):
                xml_file_name = filename[:-4] + ".xml"
                if xml_file_name in doc_dict:
                    document = doc_dict[xml_file_name]
                    # Look first if there's a job for the current filename.
                    # If not, create it
                    file_job = queue_obj.search(
                        [("channel", "=", "root.voxel_status")]
                    ).filtered(lambda r: r.args == [filename, company])[:1]
                    if not file_job:
                        error_msg = (
                            document.with_context(company_id=company.id)
                            .with_delay()
                            ._update_error_status(company, filename)
                        )
                        # search queue job to add it to voxel job list
                        document.voxel_job_ids |= queue_obj.search(
                            [("uuid", "=", error_msg.uuid)], limit=1
                        )
        # Update state of accepted documents
        (processed - with_errors).write({"voxel_state": "accepted"})

    @job(default_channel="root.voxel_status")
    def _update_error_status(self, company, filename):
        processing_error_log = self._read_voxel_document(
            "Error", company, filename, "ISO-8859-1"
        )
        # Update state of documents with errors
        self.write(
            {
                "processing_error": processing_error_log,
                "voxel_state": "processing_error",
            }
        )
        # Delete error files from Voxel
        self._delete_voxel_document("Error", filename, company)
        self._delete_voxel_document("Error", filename[:-4] + ".xml", company)
        self._delete_voxel_document("Error", filename[:-4] + ".utlog", company)

    # Import methods
    # --------------
    def enqueue_import_voxel_documents(self, company):
        queue_job_obj = self.env["queue.job"]
        # list document names
        voxel_filenames = self._list_voxel_document_filenames("Inbox", company)
        # iterate the list to import documents one by one
        for voxel_filename in voxel_filenames:
            # Look first if there's a job for the current filename.
            # If not, create it
            file_job = queue_job_obj.search(
                [("channel", "=", "root.voxel_import")]
            ).filtered(lambda r: r.args == [voxel_filename, company])[:1]
            if not file_job:
                self.with_context(
                    company_id=company.id
                ).with_delay()._import_voxel_document(voxel_filename, company)

    @job(default_channel="root.voxel_import")
    def _import_voxel_document(self, voxel_filename, company):
        content = self._read_voxel_document("Inbox", company, voxel_filename)
        # call method that parse and create the document from the content
        doc = self.create_document_from_xml(content, voxel_filename, company)
        if doc:
            # write file content in the created object
            doc.write({"voxel_xml_report": content, "voxel_filename": voxel_filename})
            # Delete file from Voxel
            self._delete_voxel_document("Inbox", voxel_filename, company)

    def create_document_from_xml(self, xml_content, voxel_filename, company):
        """ This method must be overwritten by the model that use
        `enqueue_import_voxel_documents` method """
        return False

    # API request methods
    # --------------------
    def _request_to_voxel(
        self, request_method, folder, company=None, voxel_filename=None, data=None
    ):
        login = self.get_voxel_login(company)
        if not login:
            raise Exception
        url = urljoin(login.url, folder)
        url += url.endswith("/") and "" or "/"
        response = request_method(
            url=urljoin(url, voxel_filename),
            auth=(login.user, login.password),
            data=data,
        )
        _logger.debug("Voxel request response: %s", str(response))
        if response.status_code != 200:
            response.raise_for_status()
        return response

    def _send_voxel_report(self, folder, file_name, file_data):
        try:
            self._request_to_voxel(
                requests.put, folder, voxel_filename=file_name, data=file_data
            )
        except Exception:
            new_cr = Registry(self.env.cr.dbname).cursor()
            env = api.Environment(new_cr, self.env.uid, self.env.context)
            record = env[self._name].browse(self.id)
            record.voxel_state = "sent_errors"
            new_cr.commit()
            new_cr.close()
            raise

    def _list_voxel_document_filenames(self, folder, company):
        try:
            response = self._request_to_voxel(requests.get, folder, company)
        except Exception:
            raise Exception("Error reading '{}' folder from Voxel".format(folder))
        # if no error, return list of documents file names
        content = response.content
        return content and content.decode("utf-8").split("\n") or []

    def _read_voxel_document(self, folder, company, filename, encoding="utf-8"):
        try:
            response = self._request_to_voxel(requests.get, folder, company, filename)
        except Exception:
            raise Exception(
                "Error reading document {} from folder {}".format(filename, folder)
            )
        # Getting xml content with utf8 there are characters that can not
        # be decoded, so 'ISO-8859-1' is used
        return response.content.decode(encoding)

    def _delete_voxel_document(self, folder, voxel_filename, company):
        try:
            self._request_to_voxel(requests.delete, folder, company, voxel_filename)
        except Exception:
            raise Exception(
                "Error deleting document {} from folder {}".format(
                    voxel_filename, folder
                )
            )

    # auxiliary methods
    # -----------------
    def _get_voxel_filename(self):
        self.ensure_one()
        document_type = self.get_document_type()
        date_time_seq = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return "{}_{}.xml".format(document_type, date_time_seq)

    def _cancel_voxel_jobs(self):
        # Remove not started jobs
        not_started_jobs = self.env["queue.job"]
        for queue in self.mapped("voxel_job_ids"):
            if queue.state == "started":
                raise exceptions.Warning(
                    _(
                        "This operation cannot be performed because there are "
                        "jobs running therefore cannot be unlinked."
                    )
                )
            else:
                not_started_jobs |= queue
        not_started_jobs.unlink()
        # set voxel state to cancelled
        self.write({"voxel_state": "cancelled"})

    def get_voxel_login(self, company=None):
        """ This method must be overwritten by the model that inherit from
        voxel.mixin"""
        return self.env["voxel.login"]

    def _get_customer_product_sku(self, product, partner):
        customerinfo = self.env["product.customerinfo"].search(
            [
                ("name", "=", partner.id),
                "|",
                ("product_id", "=", product.id),
                "&",
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("product_id", "=", False),
            ],
            limit=1,
            order="product_id, sequence",
        )
        return customerinfo.product_code
