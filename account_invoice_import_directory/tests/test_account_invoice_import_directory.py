# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from os import path
import tempfile
import mock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestInvoiceImportDirectory(TransactionCase):

    def setUp(self):
        super(TestInvoiceImportDirectory, self).setUp()

        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        # Create a fake file to load
        self.file_name = 'test.txt'
        self.file_path = path.join(self.test_dir, self.file_name)
        f = open(self.file_path, 'w')
        f.write('Test')

        # Configure the company
        self.main_company = self.env.ref('base.main_company')
        Users = self.env['res.users'].with_context(
            {'no_reset_password': True, 'mail_create_nosubscribe': True})
        user_group_invoice = self.env.ref('account.group_account_invoice')
        self.techuser = Users.create({
            'name': 'Technical User For Main Company',
            'login': 'tech_user',
            'email': 'tech_u@example.com',
            'notify_email': 'none',
            'groups_id': [(6, 0, [user_group_invoice.id])]})
        self.main_company.write({'user_tech_id': self.techuser.id})

        # Create a import configuration
        vals = {
            'name': 'Test Directory Configuration',
            'directory_path': self.test_dir,
            'company_id': self.main_company.id,
            'after_import': 'delete'}
        self.config = self.env['account.invoice.import.directory'].create(vals)

    def test_import_from_directory_wrong_path(self):
        """
            Test Case:
            Try to import an invoice file from an unknown directory
        """
        self.config.write({'directory_path': '/dummy'})

        with self.assertRaises(ValidationError):
            self.config._iter_directory()

    def test_import_from_directory_wrong_backup_path(self):
        """
            Test Case:
            Try to import an invoice file and move it to an unknown backup
            directory
        """
        self.config.write({'after_import': 'backup',
                           'backup_path': '/dummy'})

        with self.assertRaises(ValidationError):
            self.config._iter_directory()

    def test_import_from_directory_delete(self):
        """
            Test Case:
            Try to import an invoice file and delete it after processing
        """
        self.config._iter_directory()
        self.assertFalse(path.exists(self.file_path))

        job_name = 'Import Vendor Invoice from file %s' % self.file_name
        qjob = self.env['queue.job'].search(
            [('name', '=', job_name)])
        self.assertTrue(qjob)

    def test_import_from_directory_backup(self):
        """
            Test Case:
            Try to import an invoice file and move it to a backup directory
            after processing
        """
        backup_dir = tempfile.mkdtemp()
        self.config.write({'after_import': 'backup',
                           'backup_path': backup_dir})

        file_backup_path = path.join(backup_dir, self.file_name)

        self.config._iter_directory()
        self.assertFalse(path.exists(self.file_path))
        self.assertTrue(path.exists(file_backup_path))

        job_name = 'Import Vendor Invoice from file %s' % self.file_name
        qjob = self.env['queue.job'].search(
            [('name', '=', job_name)])
        self.assertTrue(qjob)

    def test_action_batch_import(self):
        """
            Test Case:
            Launch the import method triggered by the job and check that all
            required methods are called
        """
        f = open(self.file_path)
        data = f.read()
        wizard = self.env['account.invoice.import']
        with mock.patch.object(wizard.__class__, 'parse_invoice') as \
                mocked_parse,\
                mock.patch.object(wizard.__class__, 'create_invoice_action') \
                as mocked_create_invoice:
            self.config.action_batch_import(self.file_name, data)
            self.assertEqual(mocked_parse.call_count, 1)
            self.assertEqual(mocked_create_invoice.call_count, 1)

    def test_scheduler_import_invoice(self):
        """
            Test Case:
            Launch the scheduler method used by the cron and check that all
            required methods are called
        """
        config_model = self.env['account.invoice.import.directory']
        with mock.patch.object(config_model.__class__, '_iter_directory') as \
                mocked_iter:
            config_model._scheduler_import_invoice()
            self.assertEqual(mocked_iter.call_count, 1)
