# Copyright 2015-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from facturx import get_facturx_level, xml_check_schematron
from lxml import etree

from odoo.tests.common import TransactionCase

FACTURX_LEVELS = ("minimum", "basicwl", "basic", "en16931", "extended")

RAM_NS = (
    "urn:un:unece:uncefact:data:standard:"
    "ReusableAggregateBusinessInformationEntity:100"
)
NSMAP = {"ram": RAM_NS}


class TestFacturXInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.product1 = cls.env.ref("product.product_product_4")
        cls.product2 = cls.env.ref("product.product_product_1")
        cls.env.user.partner_id.email = "billing@example.com"
        # Force DE country and checksum-valid VAT identifiers on
        # seller and buyer so the schematron does not flag BR-CO-26
        # ("seller identifier required") and the cascading BR-S-02
        # rules whenever invoice lines use VAT category 'S'. Both
        # values pass the python-stdnum mod-11 checksum that
        # base_vat.check_vat enforces. DE123456788 is the canonical
        # placeholder Odoo itself shows in its validation error
        # message; DE129273398 is Siemens AG's real public UStId.
        de_country = cls.env.ref("base.de")
        cls.company.partner_id.write(
            {
                "country_id": de_country.id,
                "vat": "DE123456788",
            }
        )
        buyer = cls.env.ref("base.res_partner_2")
        buyer.write(
            {
                "country_id": de_country.id,
                "vat": "DE129273398",
            }
        )
        cls.proprietary_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "acc_number": "ACC-FACTURX-0001",
                "acc_type": "bank",
            }
        )
        sale_taxes = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "sale"),
                "|",
                ("unece_type_id", "=", False),
                ("unece_categ_id", "=", False),
            ]
        )
        sale_taxes.write(
            {
                "unece_type_id": cls.env.ref("account_tax_unece.tax_type_vat").id,
                "unece_categ_id": cls.env.ref("account_tax_unece.tax_categ_s").id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "move_type": "out_invoice",
                "partner_id": cls.env.ref("base.res_partner_2").id,
                "currency_id": cls.company.currency_id.id,
                "partner_bank_id": cls.proprietary_bank.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product1.id,
                            "quantity": 12,
                            "price_unit": 42.42,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product2.id,
                            "quantity": 2,
                            "price_unit": 12.34,
                        },
                    ),
                ],
            }
        )
        cls.invoice.action_post()
        cls.invoice.partner_bank_id = cls.proprietary_bank

    def _generate_xml_root(self, invoice=None, level="en16931"):
        invoice = invoice or self.invoice
        self.company.write({"facturx_level": level})
        xml_bytes, fx_level = invoice.generate_facturx_xml()
        self.assertEqual(fx_level, level)
        return etree.fromstring(xml_bytes)

    def test_deep_customer_invoice(self):
        # Bug in Basic XSD: missing CountrySubDivisionName
        # I reported it to FNFE-MPE on 24/10/2021
        # In the meantime, we want to avoid the bug:
        self.company.partner_id.state_id = False
        self.invoice.partner_id.state_id = False
        if self.company.xml_format_in_pdf_invoice != "factur-x":
            self.company.write({"xml_format_in_pdf_invoice": "factur-x"})
        # inv_report = self.env.ref("account.account_invoices").with_context(
        #    force_report_rendering=True
        # )
        for level in ["minimum", "basicwl", "basic", "en16931", "extended"]:
            self.company.write({"facturx_level": level})
            # Travis tests get stalled on this line
            # Maybe it's not possible to render a PDF on Travis... I don't know
            # pdf_content, pdf_ext = inv_report._render_qweb_pdf(
            #    res_ids=[self.invoice.id]
            # )
            # xml_filename, xml_string = get_facturx_xml_from_pdf(
            #    pdf_content, check_xsd=True
            # )
            # self.assertTrue(xml_filename, "factur-x.xml")
            # xml_root = etree.fromstring(xml_string)
            # facturx_level = get_facturx_level(xml_root)
            # self.assertEqual(facturx_level, level)
            xml_bytes, fx_level = self.invoice.generate_facturx_xml()
            self.assertEqual(fx_level, level)
            xml_root = etree.fromstring(xml_bytes)
            facturx_level = get_facturx_level(xml_root)
            self.assertEqual(facturx_level, level)

    def test_email_uriid_has_no_schemeid(self):
        xml_root = self._generate_xml_root(level="en16931")
        uriid_nodes = xml_root.xpath(
            "//ram:DefinedTradeContact/"
            "ram:EmailURIUniversalCommunication/"
            "ram:URIID",
            namespaces=NSMAP,
        )
        self.assertTrue(uriid_nodes, "Expected seller email URIID in EN16931 XML")
        self.assertEqual(uriid_nodes[0].text, "billing@example.com")
        self.assertNotIn("schemeID", uriid_nodes[0].attrib)

    def test_credit_transfer_uses_proprietary_id_for_non_iban_account(self):
        xml_root = self._generate_xml_root(level="en16931")
        proprietary_nodes = xml_root.xpath(
            "//ram:SpecifiedTradeSettlementPaymentMeans/"
            "ram:PayeePartyCreditorFinancialAccount/"
            "ram:ProprietaryID",
            namespaces=NSMAP,
        )
        iban_nodes = xml_root.xpath(
            "//ram:SpecifiedTradeSettlementPaymentMeans/"
            "ram:PayeePartyCreditorFinancialAccount/"
            "ram:IBANID",
            namespaces=NSMAP,
        )

        self.assertTrue(
            proprietary_nodes,
            "Expected ProprietaryID for non-IBAN creditor account",
        )
        self.assertEqual(
            proprietary_nodes[0].text,
            self.proprietary_bank.sanitized_acc_number,
        )
        self.assertFalse(iban_nodes, "IBANID should not be generated for non-IBAN bank")

    def test_credit_transfer_without_account_skips_payment_means(self):
        """BT-84 (payee account identifier) is optional in EN16931
        (cardinality 0..1). When the invoice has no recipient bank
        account, the module must NOT raise and must NOT emit a
        credit-transfer ``SpecifiedTradeSettlementPaymentMeans`` block
        (which would trip BR-50 / BR-61 / BR-CO-27). The whole optional
        BG-16 group is skipped and the document stays schematron-valid
        on every profile.
        """
        invoice = self.invoice.copy(default={"partner_bank_id": False})
        invoice.action_post()
        # partner_bank_id is a stored compute that can re-fire on post;
        # make sure the no-bank precondition actually holds.
        invoice.partner_bank_id = False
        self.assertFalse(invoice.partner_bank_id)

        # Must not raise and must stay schematron-valid on all profiles.
        self._assert_schematron_passes(invoice)

        # No payee creditor financial account (BT-84) must be emitted.
        root = self._generate_xml_root(invoice=invoice, level="en16931")
        payee_accounts = root.xpath(
            "//ram:SpecifiedTradeSettlementPaymentMeans/"
            "ram:PayeePartyCreditorFinancialAccount",
            namespaces=NSMAP,
        )
        self.assertFalse(
            payee_accounts,
            "No PayeePartyCreditorFinancialAccount (BT-84) must be "
            "emitted when the invoice has no recipient bank account.",
        )

    # ------------------------------------------------------------------
    # Schematron meta-test (silver bullet)
    # ------------------------------------------------------------------
    # Runs the official factur-x schematron over the generated XML for
    # every profile. The XSD-only check does not catch business-rule
    # violations such as BR-FX-EN-04 (delivery date) or BR-CO-27
    # (IBAN/ProprietaryID). The schematron does. Each fixture below
    # stresses a different combination known to trigger schematron
    # errors with the current OCA module against factur-x 4.x.

    def _assert_schematron_passes(self, invoice, levels=FACTURX_LEVELS):
        """Run xml_check_schematron over all requested profiles.

        Collects per-profile failures so that one test run reports
        every broken profile at once instead of stopping at the first.
        """
        failures = []
        for level in levels:
            self.company.write({"facturx_level": level})
            xml_bytes, fx_level = invoice.generate_facturx_xml()
            self.assertEqual(fx_level, level)
            try:
                xml_check_schematron(
                    xml_bytes, flavor="factur-x", level=level
                )
            except Exception as exc:
                failures.append((level, str(exc)))
        if failures:
            report = "\n\n".join(
                f"--- {lvl.upper()} ---\n{msg}" for lvl, msg in failures
            )
            self.fail(
                f"Schematron failed for {len(failures)} profile(s):\n\n"
                f"{report}"
            )

    def test_schematron_default_invoice_de_de(self):
        """Default fixture (2 lines, no discount, ProprietaryID account).

        Should pass on every profile after the schematron-related
        fixes are in place. Currently expected to fail at least with
        BR-FX-EN-04 because the fixture has no delivery_date set and
        the upstream PR #1320 fix uses invoice_date as fallback only
        when delivery_date is not available — which it is not for this
        fixture.
        """
        self._assert_schematron_passes(self.invoice)

    def test_schematron_invoice_with_line_discount(self):
        """Lines with discount > 0 trigger the GrossPrice/AppliedTradeAllowanceCharge
        block. EN16931 and BASIC schematron mark CalculationPercent and
        BasisAmount as 'not used' inside that block; only ChargeIndicator
        and ActualAmount are allowed there. EXTENDED permits them.

        Currently expected to fail on BASIC and EN16931.
        """
        # account.move.partner_bank_id is a stored compute with
        # @api.depends('partner_id', 'company_id') and copy=False, so it
        # gets recomputed (to empty, for our bank-less customer) on
        # copy() and can re-fire on state changes. We mirror the same
        # workaround setUpClass already uses for cls.invoice and
        # re-assign the proprietary bank explicitly after copy() and
        # again after action_post(). This keeps a realistic, complete
        # invoice (with BT-84) so this test isolates the discount /
        # AppliedTradeAllowanceCharge behaviour rather than the separate
        # no-bank code path (covered by
        # test_credit_transfer_without_account_skips_payment_means).
        invoice = self.invoice.copy()
        invoice.partner_bank_id = self.proprietary_bank
        for line in invoice.invoice_line_ids:
            line.discount = 10.0
        invoice.action_post()
        invoice.partner_bank_id = self.proprietary_bank
        self._assert_schematron_passes(invoice)

    def test_subscription_line_period_emits_billing_specified_period(self):
        """When invoice lines carry deferred_start_date / deferred_end_date
        (Enterprise feature representing a subscription / service period)
        the line-level XML must contain a ram:BillingSpecifiedPeriod block
        with ram:StartDateTime and ram:EndDateTime (BG-26, Invoice line
        period). Without this mapping the deferred-revenue dates are
        silently dropped from the Factur-X export, even though the
        schematron still passes via BT-72 (header delivery date).

        Currently expected to fail because BillingSpecifiedPeriod is not
        emitted from deferred_*-fields by the module.
        """
        if "deferred_start_date" not in self.env["account.move.line"]._fields:
            self.skipTest(
                "deferred_start_date / deferred_end_date are not available "
                "in this database (requires Enterprise account_accountant)."
            )
        invoice = self.invoice.copy()
        invoice.partner_bank_id = self.proprietary_bank
        # invoice.copy() returns a draft with invoice_date == False;
        # take the source invoice's posted date as a deterministic
        # reference for the synthetic service period.
        invoice.invoice_date = self.invoice.invoice_date
        start = invoice.invoice_date.replace(day=1)
        end = start + timedelta(days=29)
        for line in invoice.invoice_line_ids:
            line.write(
                {
                    "deferred_start_date": start,
                    "deferred_end_date": end,
                }
            )
        invoice.action_post()
        invoice.partner_bank_id = self.proprietary_bank
        # Schematron must still pass; BG-26 is structural enrichment, not
        # a validation gate (BR-FX-EN-04 is already satisfied via BT-72).
        self._assert_schematron_passes(invoice)
        # And the actual XML must contain the period block, one per line.
        root = self._generate_xml_root(invoice=invoice, level="en16931")
        period_nodes = root.findall(".//{%s}BillingSpecifiedPeriod" % RAM_NS)
        self.assertEqual(
            len(period_nodes),
            len(invoice.invoice_line_ids),
            "Expected one BillingSpecifiedPeriod per subscription line "
            "(%d lines), got %d nodes."
            % (len(invoice.invoice_line_ids), len(period_nodes)),
        )
        # Every period node must carry both Start and End DateTime.
        for period in period_nodes:
            start_nodes = period.findall("{%s}StartDateTime" % RAM_NS)
            end_nodes = period.findall("{%s}EndDateTime" % RAM_NS)
            self.assertEqual(len(start_nodes), 1)
            self.assertEqual(len(end_nodes), 1)

    def test_delivery_date_auto_set_from_period_carried_to_bt72(self):
        """End-to-end verkettung: Track 1
        (`account_invoice_delivery_date_from_period`) auto-fills
        ``delivery_date`` from the latest line period end, and Track 2
        (the `_cii_get_delivery_date` fix in this module) carries that
        value into BT-72.

        This is the only test in the suite that exercises *both*
        modules together; the isolated tests in each module cover only
        their own half. Skipped if the period-derivation module is not
        installed in the database.
        """
        if "deferred_start_date" not in self.env["account.move.line"]._fields:
            self.skipTest(
                "deferred_start_date / deferred_end_date are not available "
                "in this database (requires Enterprise account_accountant)."
            )
        helper_installed = self.env["ir.module.module"].search(
            [
                ("name", "=", "account_invoice_delivery_date_from_period"),
                ("state", "=", "installed"),
            ],
            limit=1,
        )
        if not helper_installed:
            self.skipTest(
                "account_invoice_delivery_date_from_period is not installed "
                "in this database; the verkettung Track 1 → Track 2 cannot "
                "be exercised."
            )
        invoice = self.invoice.copy()
        invoice.partner_bank_id = self.proprietary_bank
        invoice.invoice_date = self.invoice.invoice_date
        # Two subscription lines with distinct period ends — the latest
        # one (period_end_late) must win per UStG § 13 (see ADR
        # 2026-05-11_adr_delivery-date-aus-periode-ende.md).
        period_end_early = invoice.invoice_date + timedelta(days=10)
        period_end_late = invoice.invoice_date + timedelta(days=42)
        lines = list(invoice.invoice_line_ids)
        self.assertGreaterEqual(
            len(lines),
            2,
            "Test fixture invariant: source invoice must have at least "
            "two lines so the max() over period ends is non-trivial.",
        )
        lines[0].write(
            {
                "deferred_start_date": invoice.invoice_date,
                "deferred_end_date": period_end_early,
            }
        )
        lines[1].write(
            {
                "deferred_start_date": invoice.invoice_date,
                "deferred_end_date": period_end_late,
            }
        )
        # Critical pre-condition: do NOT set delivery_date manually.
        # The whole point is that Track 1's _post() override fills it
        # from the line periods automatically.
        self.assertFalse(
            invoice.delivery_date,
            "Test pre-condition: delivery_date must be empty before "
            "posting so we can prove Track 1 fills it from periods.",
        )
        invoice.action_post()
        invoice.partner_bank_id = self.proprietary_bank
        # Track 1 assertion: _post() override picked the latest end date.
        self.assertEqual(
            invoice.delivery_date,
            period_end_late,
            "Track 1: _post() override must auto-set delivery_date to "
            "max(deferred_end_date) = %s; got %r."
            % (period_end_late, invoice.delivery_date),
        )
        # Track 2 assertion: that auto-set value reaches BT-72 in the XML.
        self._assert_schematron_passes(invoice)
        root = self._generate_xml_root(invoice=invoice, level="en16931")
        occurrence = root.find(
            ".//{%s}ActualDeliverySupplyChainEvent/{%s}OccurrenceDateTime"
            % (RAM_NS, RAM_NS)
        )
        self.assertIsNotNone(
            occurrence,
            "BT-72 OccurrenceDateTime element is missing from the XML.",
        )
        bt72_text = list(occurrence)[0].text
        self.assertEqual(
            bt72_text,
            period_end_late.strftime("%Y%m%d"),
            "Track 2 (verkettung): BT-72 must carry the auto-set "
            "delivery_date (%s, format YYYYMMDD = %s); got %r. "
            "Either Track 1 did not write delivery_date (check that "
            "account_invoice_delivery_date_from_period._post() ran), "
            "or Track 2's _cii_get_delivery_date() is dropping "
            "delivery_date again."
            % (
                period_end_late,
                period_end_late.strftime("%Y%m%d"),
                bt72_text,
            ),
        )

    def test_delivery_date_carried_to_bt72_when_set_explicitly(self):
        """When ``account.move.delivery_date`` is set to a value other
        than ``invoice_date`` (e.g. by a subscription module that
        derives it from line periods, or by the user), BT-72
        (``ActualDeliverySupplyChainEvent/OccurrenceDateTime``) in the
        Factur-X XML must carry the ``delivery_date``, NOT the
        ``invoice_date``.

        Currently expected to fail because ``_cii_get_delivery_date()``
        returns ``self.invoice_date`` unconditionally and ignores the
        standard Odoo ``delivery_date`` field.
        """
        invoice = self.invoice.copy()
        invoice.partner_bank_id = self.proprietary_bank
        # invoice.copy() returns a draft with invoice_date == False;
        # take the source invoice's posted date as a deterministic
        # baseline.
        invoice.invoice_date = self.invoice.invoice_date
        explicit_delivery = invoice.invoice_date + timedelta(days=15)
        invoice.delivery_date = explicit_delivery
        invoice.action_post()
        invoice.partner_bank_id = self.proprietary_bank
        # Schematron must still pass; this test is about the SEMANTIC
        # content of BT-72, not its presence.
        self._assert_schematron_passes(invoice)
        # BT-72 lives at
        # ApplicableHeaderTradeDelivery/ActualDeliverySupplyChainEvent/
        # OccurrenceDateTime/udt:DateTimeString. The DateTimeString
        # element is in the UDT namespace; using "*" wildcards lets us
        # ignore that detail and check the actual text content.
        root = self._generate_xml_root(invoice=invoice, level="en16931")
        occurrence = root.find(
            ".//{%s}ActualDeliverySupplyChainEvent/{%s}OccurrenceDateTime"
            % (RAM_NS, RAM_NS)
        )
        self.assertIsNotNone(
            occurrence,
            "BT-72 OccurrenceDateTime element is missing from the XML.",
        )
        date_string_elements = list(occurrence)
        self.assertEqual(
            len(date_string_elements),
            1,
            "Expected exactly one DateTimeString child under "
            "OccurrenceDateTime; got %d." % len(date_string_elements),
        )
        bt72_text = date_string_elements[0].text
        self.assertEqual(
            bt72_text,
            explicit_delivery.strftime("%Y%m%d"),
            "BT-72 must carry delivery_date (%s, format YYYYMMDD = %s); "
            "got %r. The hook _cii_get_delivery_date() is likely still "
            "returning self.invoice_date and ignoring the standard "
            "Odoo delivery_date field."
            % (
                explicit_delivery,
                explicit_delivery.strftime("%Y%m%d"),
                bt72_text,
            ),
        )
