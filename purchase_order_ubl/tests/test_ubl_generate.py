# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from .common import PurchaseOrderUblMixin


class TestUblGenerate(PurchaseOrderUblMixin, TransactionCase):
    """Direct test of ``generate_ubl_xml_string`` on ``purchase.order``.

    No EDI framework: we call the UBL helpers directly to make sure the
    generated XML is well formed and respects the official UBL XSD for
    both ``Order`` (confirmed PO) and ``RequestForQuotation`` (RFQ),
    against UBL versions 2.1 and 2.2.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls._setup_purchase_ubl_records()

    def _generate(self, doc_type, version):
        return self.order.generate_ubl_xml_string(doc_type, version=version)

    def test_generate_order_confirmed(self):
        self.order.button_confirm()
        self.assertEqual(self.order.state, "purchase")
        self.assertEqual(self.order.get_ubl_purchase_order_doc_type(), "order")
        for version in ("2.1", "2.2"):
            with self.subTest(version=version):
                xml_string = self._generate("order", version)
                self._assert_valid_ubl_xml(xml_string, "Order", version)

    def test_generate_rfq(self):
        self.assertIn(self.order.state, self.order.get_rfq_states())
        self.assertEqual(self.order.get_ubl_purchase_order_doc_type(), "rfq")
        for version in ("2.1", "2.2"):
            with self.subTest(version=version):
                xml_string = self._generate("rfq", version)
                self._assert_valid_ubl_xml(xml_string, "RequestForQuotation", version)

    def test_generate_taxes_included_by_default(self):
        """By default ``ClassifiedTaxCategory`` is rendered for each item."""
        self.order.button_confirm()
        xml_string = self._generate("order", "2.1")
        parsed = self._assert_valid_ubl_xml(xml_string, "Order", "2.1")
        tax_nodes = self._classified_tax_categories(parsed)
        self.assertTrue(
            tax_nodes,
            "Expected at least one ClassifiedTaxCategory in default UBL output",
        )

    def test_generate_skip_taxes_ctx(self):
        """``ubl_add_item__skip_taxes`` removes ClassifiedTaxCategory nodes."""
        self.order.button_confirm()
        xml_string = self.order.with_context(
            ubl_add_item__skip_taxes=True
        ).generate_ubl_xml_string("order", version="2.1")
        parsed = self._assert_valid_ubl_xml(xml_string, "Order", "2.1")
        tax_nodes = self._classified_tax_categories(parsed)
        self.assertFalse(
            tax_nodes,
            "ClassifiedTaxCategory must be skipped when "
            "ubl_add_item__skip_taxes is set in context",
        )
