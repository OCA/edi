# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_open


class CommonAccountEdiUnece(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "TEST Tax",
                "amount": 20,
                "amount_type": "percent",
            }
        )
        cls.journal = cls.env.ref("account.1_bank")
        cls.inbound_payment_method = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        cls.inbound_payment_method_line = cls.inbound_payment_method.line_ids.filtered(
            lambda line: line.journal_id == cls.journal
        )
        cls.outbound_payment_method = cls.env.ref(
            "account.account_payment_method_manual_out"
        )
        cls.outbound_payment_method_line = (
            cls.outbound_payment_method.line_ids.filtered(
                lambda line: line.journal_id == cls.journal
            ).copy({"journal_id": cls.env.ref("account.1_purchase").id})
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "TEST",
                "email": "test@example.net",
                "property_inbound_payment_method_line_id": (
                    cls.inbound_payment_method_line.id
                ),
            }
        )

    def _create_out_invoice(self, post=False):
        vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": "TEST",
                        "price_unit": 100,
                        "quantity": 1,
                        "tax_ids": self.tax.ids,
                    }
                )
            ],
        }
        invoice = self.env["account.move"].create(vals)
        if post:
            invoice.action_post()
        return invoice

    def _create_in_invoice(self):
        vals = {
            "move_type": "in_invoice",
            "partner_id": self.partner.id,
        }
        return self.env["account.move"].create(vals)

    def _import_invoice_xml_file(self, invoice, file_path):
        """Update `invoice` by importing `file_path` XML file data."""
        with file_open(file_path, mode="rb") as file_:
            content = file_.read()
        invoice.ubl_cii_xml_file = base64.b64encode(content)
        file_data = invoice.ubl_cii_xml_id._unwrap_edi_attachments()[0]
        decoder = invoice._get_edi_decoder(file_data)
        decoder(invoice, file_data)
