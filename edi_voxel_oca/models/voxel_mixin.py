# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
import logging
import requests
from lxml import etree
from odoo import api, fields, models

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
        company = self.env['res.company']._company_default_get()
        eta = company._get_voxel_report_eta()
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
            new_delay = record.with_delay(
                eta=eta)._get_and_send_voxel_report(report_name)
            job = queue_obj.search([
                ('uuid', '=', new_delay.uuid)
            ], limit=1)
            record.voxel_job_ids |= job

    @job(default_channel='root.voxel')
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
        company = self.env['res.company']._company_default_get()
        outbox_url = "%s/Outbox" % company.voxel_api_url
        user = company.voxel_api_user
        password = company.voxel_api_password
        file_name = self._get_voxel_filename()
        try:
            response = requests.put(
                "%s/%s" % (outbox_url, file_name),
                data=file_data,
                auth=(user, password))
            self.voxel_state = 'sent'
            _logger.info("Voxel request response: %s", str(response))
        except Exception:
            self.voxel_state = 'sent_errors'
            raise

    def _get_outbox_url(self):
        company = self.env['res.company']._company_default_get()
        return "%s/Outbox" % company.voxel_api_url

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
