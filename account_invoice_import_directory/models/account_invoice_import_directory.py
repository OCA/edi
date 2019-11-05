# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job

BASE_CHANNEL = 'root.account_invoice_import'


def source_name(directory, file_name):
    """helper to get the full name"""
    return directory + '/' + file_name


class AccountInvoiceImportDirectory(models.Model):
    _name = 'account.invoice.import.directory'

    name = fields.Char(
        required=True)

    directory_path = fields.Char(
        required=True,
        help="Directory path from where you want to import invoices")

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        string='Company',
    )

    after_import = fields.Selection(
        selection=[('backup', 'Backup File'),
                   ('delete', 'Delete File')],
        default='backup',
        help="After the import, you can either delete the file either move "
             "it to a backup directory",
        required=True,
    )

    backup_path = fields.Char(
        help="Directory where you want to move the file after the import")
    attach_file_job = fields.Boolean(
        string="Attach file to job",
        default=False,
        help="Attach the file to import to the related importation job",
    )

    @api.model
    def _scheduler_import_invoice(self):
        """
            Launch the scanning for all configurations defined
        :return:
        """
        for config in self.search([]):
            config._iter_directory()

    @api.multi
    def _get_files_in_directory(self):
        """
            Load a list of all file names existing in the directory
        :return: list of file names
        """
        self.ensure_one()
        return [f for f in os.listdir(self.directory_path)]

    @api.multi
    def _after_import(self, file_name, file_path):
        """
            Manage the after_import process of an invoice file. It can be
            either deleted or moved to a backup directory depending on the
            configuration
        :param file_name: the name of the file to manage
        :param file_path: the full path of the file to manage
        :return:
        """
        self.ensure_one()
        if self.after_import == 'backup':
            if not os.path.exists(self.backup_path):
                raise ValidationError(_('Unknown backup path provided: %s'
                                        % self.backup_path))
            backup_full_name = source_name(self.backup_path,
                                           file_name)
            os.rename(file_path, backup_full_name)
        elif self.after_import == 'delete':
            os.remove(file_path)

    @api.multi
    def _iter_directory(self):
        """
            Scan the directory linked to the current configuration and launch
            a queue job for each file found. Each job will call the invoice
            import wizard.
        :return: None
        """
        self.ensure_one()
        if not os.path.exists(self.directory_path):
            raise ValidationError(_('Unknown path provided: %s'
                                    % self.directory_path))
        files = self._get_files_in_directory()

        for file_imported in files:
            file_full_name = source_name(self.directory_path,
                                         file_imported)
            with open(file_full_name) \
                    as fileobj:
                data = fileobj.read()
            description = 'Import Vendor Invoice from file %s' % file_imported
            file_content = data.encode('base64')
            job = self.with_delay(description=description).action_batch_import(
                file_imported, file_content)
            if self.attach_file_job:
                queue_job = self.env['queue.job'].search([
                    ('uuid', '=', job.uuid),
                ], limit=1)
                self._attach_file_to_job(
                    file_imported, file_content, queue_job)
            self._after_import(file_imported, file_full_name)

    @api.multi
    def _attach_file_to_job(self, filename, file_content, job):
        """
        Attach the given file to the given job
        :param filename: str
        :param file_content: base64 str
        :param job: queue.job recordset
        :return:
        """
        attach_obj = self.env['ir.attachment']
        attach = attach_obj.browse()
        if job:
            values = {
                'name': filename,
                'datas': file_content,
                'datas_fname': filename,
                'res_model': job._name,
                'res_id': job.id,
            }
            attach = self.env['ir.attachment'].create(values)
        return attach

    @job(default_channel=BASE_CHANNEL)
    def action_batch_import(self, file_name, file_content):
        """
            Method to manage the call to the invoice import wizard for each
            file found in the configuration directory
        :param file_name: Name of the file to load
        :param file_content: Content of the file to load
        :return: Result of invoice import wizard
        """
        vals = {
            'invoice_file': file_content,
            'invoice_filename': file_name}
        wiz = self.env['account.invoice.import'].create(vals)
        return wiz.import_invoice()
