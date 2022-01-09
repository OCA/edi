# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_test_helper import FakeModelLoader


class InvoiceDownloadCommon():

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import AccountInvoiceDownloadConfigFake

        cls.loader.update_registry((AccountInvoiceDownloadConfigFake,))

        cls.config_obj = cls.env["account.invoice.download.config"]
        cls.log_obj = cls.env["account.invoice.download.log"]
        cls.import_config_obj = cls.env["account.invoice.import.config"]
        cls.wizard_obj = cls.env["account.invoice.download.credentials"]
        cls.cron = cls.env.ref(
            "account_invoice_download.account_invoice_download_cron")
        cls.account_invoice = cls.env["account.invoice"]
        cls.partner = cls.env.ref("base.res_partner_2")

        cls.expense_account = cls.env['account.account'].create({
            'code': '612AII',
            'name': 'expense account invoice import',
            'user_type_id':
            cls.env.ref('account.data_account_type_expenses').id,
        })
        purchase_tax_vals = {
            'name': 'Test 1% VAT',
            'description': 'ZZ-VAT-buy-1.0',
            'type_tax_use': 'purchase',
            'amount': 1,
            'amount_type': 'percent',
            'unece_type_id': cls.env.ref('account_tax_unece.tax_type_vat').id,
            'unece_categ_id': cls.env.ref('account_tax_unece.tax_categ_s').id,
            'account_id': cls.expense_account.id,
            'refund_account_id': cls.expense_account.id,
        }
        cls.purchase_tax = cls.env['account.tax'].create(purchase_tax_vals)

        vals = {
            "name": "Default Config",
            "invoice_line_method": '1line_no_product',
            "partner_id": cls.partner.id,
            "account_id": cls.expense_account.id,
            "tax_ids": [(6, 0, cls.purchase_tax.ids)],
            "download_config_ids": [(0, 0, {
                "name": "Default Partner",
            })],
        }
        cls.default_config = cls._create_config(vals)
        cls.default_config_line = cls.default_config.download_config_ids[0]

    @classmethod
    def _get_parsed_invoice(cls):
        # Minimum values to get invoice imported
        return {
            "type": "in_invoice",
            "attachments": {"Vendor Bill - BILL_2022_0002.pdf": None},
            "amount_untaxed": 4999,
            "amount_total": 5749.99,
        }

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def _create_config(cls, vals):
        return cls.import_config_obj.create(vals)
