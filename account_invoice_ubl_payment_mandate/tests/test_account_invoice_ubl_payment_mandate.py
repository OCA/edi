# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.account_invoice_ubl.tests.common import TestUblInvoiceMixin


@tagged("-at_install", "post_install")
class TestAccountInvoiceUblPaymentMandate(TransactionCase, TestUblInvoiceMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create({"name": "Direct Debit Partner"})
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "BE71096123456769",
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
            }
        )
        cls.mandate = cls.env["account.banking.mandate"].create(
            {
                "unique_mandate_reference": "MANDATE-REF-001",
                "partner_bank_id": cls.partner_bank.id,
                "signature_date": "2026-01-01",
                "company_id": cls.company.id,
            }
        )
        cls.direct_debit_payment_mode_49 = cls._create_payment_mode("49")
        cls.direct_debit_payment_mode = cls._create_payment_mode("59")
        cls.credit_transfer_payment_mode = cls._create_payment_mode("58")

    @classmethod
    def _create_payment_mode(cls, unece_code):
        payment_method = cls.env["account.payment.method"].create(
            {
                "name": "Test UNECE %s" % unece_code,
                "code": "test_unece_%s" % unece_code,
                "payment_type": "inbound",
                "unece_id": cls.env.ref(
                    "account_payment_unece.payment_means_%s" % unece_code
                ).id,
            }
        )
        return cls.env["account.payment.mode"].create(
            {
                "name": "Test Payment Mode %s" % unece_code,
                "company_id": cls.company.id,
                "bank_account_link": "variable",
                "payment_method_id": payment_method.id,
            }
        )

    def _create_invoice_with_mandate(self):
        invoice = self._create_invoice(validate=False)
        invoice.partner_id = self.partner
        invoice.mandate_id = self.mandate
        return invoice

    def _create_payment_means_node(self, invoice, payment_mode):
        nsmap, ns = self.env["base.ubl"]._ubl_get_nsmap_namespace("Invoice-2")
        xml_root = etree.Element("Invoice", nsmap=nsmap)
        invoice._ubl_add_payment_means(
            self.partner_bank,
            payment_mode,
            date(2026, 1, 31),
            xml_root,
            ns,
            version="2.1",
        )
        return xml_root.find(ns["cac"] + "PaymentMeans"), ns

    def test_direct_debit_adds_payment_mandate(self):
        invoice = self._create_invoice_with_mandate()
        payment_means, ns = self._create_payment_means_node(
            invoice, self.direct_debit_payment_mode
        )

        payment_mandate = payment_means.find(ns["cac"] + "PaymentMandate")
        payer_financial_account = payment_mandate.find(
            ns["cac"] + "PayerFinancialAccount"
        )

        self.assertEqual(
            payment_means.findtext(ns["cbc"] + "PaymentMeansCode"),
            "59",
        )
        self.assertEqual(
            payment_mandate.findtext(ns["cbc"] + "ID"),
            self.mandate.unique_mandate_reference,
        )
        self.assertEqual(
            payer_financial_account.findtext(ns["cbc"] + "ID"),
            self.partner_bank.sanitized_acc_number,
        )

    def test_direct_debit_code_49_adds_payment_mandate(self):
        invoice = self._create_invoice_with_mandate()
        payment_means, ns = self._create_payment_means_node(
            invoice, self.direct_debit_payment_mode_49
        )

        self.assertEqual(
            payment_means.findtext(ns["cbc"] + "PaymentMeansCode"),
            "49",
        )
        payment_mandate = payment_means.find(ns["cac"] + "PaymentMandate")
        self.assertEqual(
            payment_mandate.findtext(ns["cbc"] + "ID"),
            self.mandate.unique_mandate_reference,
        )

    def test_credit_transfer_does_not_add_payment_mandate(self):
        invoice = self._create_invoice_with_mandate()
        payment_means, ns = self._create_payment_means_node(
            invoice, self.credit_transfer_payment_mode
        )

        self.assertEqual(
            payment_means.findtext(ns["cbc"] + "PaymentMeansCode"),
            "58",
        )
        self.assertIsNone(payment_means.find(ns["cac"] + "PaymentMandate"))

    def test_direct_debit_without_mandate_raises(self):
        invoice = self._create_invoice(validate=False)

        with self.assertRaises(UserError):
            self._create_payment_means_node(invoice, self.direct_debit_payment_mode)
