# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _import_fill_invoice_form(self, journal, tree, invoice, qty_factor):
        """
        automatically match the invoice with a purchase order

        - disable standard purchase matching to avoid conflicts
        - only apply for vendor bills
        - use invoice_origin (UBL OrderReference) to find the related PO
        """
        invoice = invoice.with_context(no_purchase_set=True)
        res = super()._import_fill_invoice_form(journal, tree, invoice, qty_factor)
        if journal.type != "purchase":
            return res
        if not invoice.invoice_origin:
            return res
        self._match_invoice_to_purchase_order(invoice, invoice.invoice_origin)
        return res

    def _match_invoice_to_purchase_order(self, invoice, order_ref):
        """
        match the invoice with a purchase order using the order ref

        matching is done on:
        - PO name
        - Vendor reference (partner_ref)
        -o nly confirmed POs are considered
        """
        purchase_order = self.env["purchase.order"].search(
            [
                "|",
                ("name", "=", order_ref),
                ("partner_ref", "=", order_ref),
                ("state", "in", ("purchase", "done")),
            ],
            limit=1,
        )
        if not purchase_order:
            return False
        for invoice_line in invoice.invoice_line_ids:
            self._match_invoice_line_to_purchase_order_line(
                invoice_line, purchase_order.order_line
            )
        return True

    def _match_invoice_line_to_purchase_order_line(self, invoice_line, purchase_lines):
        """Match an invoice line to a purchase order line

        A match is considered when at least one of these conditions is true:
        - same product
        - same description
        - invoice line description matches the purchase line product name
        - supplier product code matches one of the vendor codes of the product
        - invoice line description matches one of the vendor product names
        """
        if invoice_line.purchase_line_id:
            return False

        for purchase_line in purchase_lines:
            product = purchase_line.product_id
            seller_product_codes = product.seller_ids.mapped("product_code")
            seller_product_names = product.seller_ids.mapped("product_name")

            same_product = product == invoice_line.product_id
            same_description = purchase_line.name == invoice_line.name
            matches_product_name = product.name == invoice_line.name
            matches_supplier_code = (
                invoice_line.supplier_product_code in seller_product_codes
            )
            matches_supplier_name = invoice_line.name in seller_product_names

            if any(
                [
                    same_product,
                    same_description,
                    matches_product_name,
                    matches_supplier_code,
                    matches_supplier_name,
                ]
            ):
                invoice_line._set_product(product)
                invoice_line.purchase_line_id = purchase_line
                break

        return True

    def _import_fill_invoice_line_form(
        self, journal, tree, invoice, invoice_line, qty_factor
    ):
        """
        add a fallback product lookup based on the supplier product code.

        the standard import logic doesn't cover this matching path, so if no product
        was found after the super call, try to resolve it from supplierinfo using the
        UBL SellerItemIdentification value
        """
        res = super()._import_fill_invoice_line_form(
            journal, tree, invoice, invoice_line, qty_factor
        )
        if invoice_line.product_id:
            return res
        supplier_product_code = self._find_value(
            "./cac:Item/cac:SellersItemIdentification/cbc:ID", tree
        )
        if not supplier_product_code:
            return res
        invoice_line.supplier_product_code = supplier_product_code
        product = self._retrieve_product_by_supplierinfo(
            invoice.partner_id, supplier_product_code
        )
        if not product:
            return res
        invoice_line._set_product(product)
        return res

    def _retrieve_product_by_supplierinfo(self, partner, supplier_product_code):
        """
        retrieve a product using supplierinfo based on:
        - supplier (partner)
        - supplier product code

        returns:
        - product variant if directly linked
        - single variant if template has only one variant
        - empty recordset otherwise
        """
        product_sinfo = self.env["product.supplierinfo"].search(
            [
                ("product_code", "=", supplier_product_code),
                ("partner_id", "=", partner.id),
            ],
            limit=1,
        )
        if product_sinfo and product_sinfo.product_id:
            return product_sinfo.product_id
        if (
            product_sinfo
            and product_sinfo.product_tmpl_id
            and len(product_sinfo.product_tmpl_id.product_variant_ids) == 1
        ):
            return product_sinfo.product_tmpl_id.product_variant_ids
        return self.env["product.product"]
