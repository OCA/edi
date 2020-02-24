# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import requests
from datetime import datetime
from lxml import etree
from odoo import api, fields, models
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class VoxelMixin(models.AbstractModel):
    _name = "voxel.mixin"
    _description = "Voxel mixin"

    voxel_state = fields.Selection(
        selection=[
            ('not_sent', 'Not sent'),
            ('sent', 'Sent'),
            ('sent_errors', 'Errors'),
            ('cancelled', 'Cancelled'),
        ],
        string="Voxel send state", default='not_sent', readonly=True,
        copy=False,
        help="Indicates the state of the Voxel report send state",
    )
    voxel_xml_report = fields.Text(
        string="XML Report",
        readonly=True)

    @api.multi
    def _get_voxel_filename(self):
        self.ensure_one()
        document_type = self.get_document_type()
        date_time_seq = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return "%s_%s.xml" % (document_type, date_time_seq)

    @api.multi
    def enqueue_voxel_report(self, report_name):
        eta = self.company_id._get_voxel_report_eta()
        queue_obj = self.env['queue.job'].sudo()
        for record in self.sudo():
            # Look first if there's a failing job. If so, retry that one
            failing_job = record.voxel_job_ids.filtered(
                lambda x: x.state == 'failed'
            )[:1]
            if failing_job:
                failing_job.voxel_requeue_sudo()
                continue
            # If not, create a new one
            new_delay = record.with_context(
                company_id=self.company_id.id
            ).with_delay(
                eta=eta
            )._get_and_send_voxel_report(report_name)

            job = queue_obj.search([
                ('uuid', '=', new_delay.uuid)
            ], limit=1)
            record.voxel_job_ids |= job

    @job(default_channel='root.voxel_export')
    @api.multi
    def _get_and_send_voxel_report(self, report_name):
        self.ensure_one()
        report = self.env.ref(report_name)
        report_xml = report.render_qweb_xml(self.ids, {})[0]
        # Remove blank spaces
        tree = etree.fromstring(report_xml,
                                etree.XMLParser(remove_blank_text=True))
        clean_report_xml = etree.tostring(tree, xml_declaration=True,
                                          encoding='UTF-8')
        self._send_voxel_report(clean_report_xml)
        # Update last xml report
        self.voxel_xml_report = report_xml

    def _send_voxel_report(self, file_data):
        file_name = self._get_voxel_filename()
        try:
            self._request_to_voxel(requests.put, voxel_filename=file_name,
                                   data=file_data)
            self.voxel_state = 'sent'
        except Exception:
            new_cr = Registry(self.env.cr.dbname).cursor()
            env = api.Environment(new_cr, self.env.uid, self.env.context)
            record = env[self._name].browse(self.id)
            record.voxel_state = 'sent_errors'
            new_cr.commit()
            new_cr.close()
            raise

    @api.multi
    def _cancel_voxel_jobs(self, jobs):
        # set voxel state to cancelled
        self.write({'voxel_state': 'cancelled'})
        # Remove not started jobs
        for queue in jobs:
            if queue.state == 'started':
                return False
            elif queue.state in ('pending', 'enqueued', 'failed'):
                queue.unlink()
        return True

    def enqueue_import_voxel_documents(self, company):
        queue_job_obj = self.env['queue.job']
        # list document names
        voxel_filenames = self._list_voxel_document_filenames(company)
        # iterate the list to import documents one by one
        for voxel_filename in voxel_filenames:
            # Look first if there's a job for the current filename.
            # If not, create it
            file_job = queue_job_obj.search([
                ('channel', '=', 'root.voxel_import')
            ]).filtered(lambda r: r.args == [voxel_filename, company])[:1]
            if not file_job:
                self.with_context(
                    company_id=company.id
                ).with_delay()._import_voxel_document(voxel_filename, company)

    def _list_voxel_document_filenames(self, company):
        try:
            response = self._request_to_voxel(requests.get, company)
        except Exception:
            _logger.exception("Error reading the inbox in Voxel")
            return []
        # if no error, return list of documents file names
        return response.content.decode('utf-8').split('\n')

    @job(default_channel='root.voxel_import')
    def _import_voxel_document(self, voxel_filename, company):
        try:
            response = self._request_to_voxel(requests.get, company,
                                              voxel_filename)
        except Exception:
            raise Exception("Error importing document %s" % (voxel_filename))
        # if no error, get xml content
        content = response.content.decode('utf-8')
        # call method that parse and create the document from the content
        doc = self.create_document_from_xml(content, voxel_filename, company)
        if doc:
            # write file content in the created object
            doc.write({
                'voxel_xml_report': content,
                'voxel_filename': voxel_filename,
            })
            # Delete file from Voxel
            # self._delete_voxel_document(voxel_filename, company)

    def _delete_voxel_document(self, voxel_filename, company):
        try:
            self._request_to_voxel(requests.delete, company, voxel_filename)
        except Exception:
            raise Exception("Error deleting document %s" % (voxel_filename))

    def _request_to_voxel(self, request_method, company=None,
                          voxel_filename=None, data=None):
        login = self.get_voxel_login(company)
        if not login:
            raise Exception
        response = request_method(
            url="/".join(filter(None, [login.url, voxel_filename])),
            auth=(login.user, login.password),
            data=data)
        _logger.debug("Voxel request response: %s", str(response))
        if response.status_code != 200:
            response.raise_for_status()
        return response

    def create_document_from_xml(self, xml_content, voxel_filename, company):
        """ This method must be overwritten by the model that use
        `enqueue_import_voxel_documents` method """
        return False

    def get_voxel_login(self, company=None):
        """ This method must be overwritten by the model that inherit from
        voxel.mixin"""
        return self.env['voxel.login']

    def _get_customer_product_sku(self, product, partner):
        customerinfo = self.env["product.customerinfo"].search([
            ("name", "=", partner.id),
            "|",
            ("product_id", "=", product.id),
            "&",
            ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ("product_id", "=", False),
        ], limit=1, order="product_id, sequence")
        return customerinfo.product_code
