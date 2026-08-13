# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import tagged
from odoo.tools.misc import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class CommonAccountEdiUnece(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.bank_journal = cls.env["account.journal"].create(
            {"type": "bank", "name": "bank", "code": "BANK"}
        )
        cls.outbound_payment_method = cls.env.ref(
            "account.account_payment_method_manual_out"
        )
        cls.outbound_payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "outbound Credit ACME Bank 2",
                "bank_account_link": "variable",
                "payment_method_id": cls.outbound_payment_method.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "TEST"})

    def _create_other_company_payment_mode(self, payment_method):
        return self.env["account.payment.mode"].create(
            {
                "name": "other company outbound Credit ACME Bank 2",
                "bank_account_link": "variable",
                "payment_method_id": payment_method.id,
                "company_id": self.company_data_2["company"].id,
            }
        )

    def _import_invoice_xml_file(self, journal, file_path):
        with file_open(file_path, "rb") as file:
            xml_attachment = self.env["ir.attachment"].create(
                {
                    "mimetype": "application/xml",
                    "name": "test_invoice.xml",
                    "raw": file.read(),
                }
            )
        move = (
            self.env["account.journal"]
            .with_context(default_journal_id=journal.id)
            ._create_document_from_attachment(xml_attachment.id)
        )
        return move
