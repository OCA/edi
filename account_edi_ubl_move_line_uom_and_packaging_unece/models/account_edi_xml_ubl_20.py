# Copyright 2026 ACSONE SA/NV, BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUbl_20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _set_invoice_line_ubl_billed_quantity_and_unece_unit_code(
        self, tree, invoice_line
    ):
        billed_quantity_xpath = (
            "./{*}InvoicedQuantity"
            if invoice_line.move_id.move_type in ("in_invoice", "out_invoice")
            else "./{*}CreditedQuantity"
        )
        billed_quantity_node = tree.find(billed_quantity_xpath)
        if billed_quantity_node is None:
            return
        invoice_line.ubl_billed_quantity = float(billed_quantity_node.text)
        unit_code = billed_quantity_node.attrib.get("unitCode")
        if unit_code:
            invoice_line.ubl_unece_unit_code = unit_code

    def _set_invoice_ubl_price_unit(self, tree, invoice_line):
        price_unit_node = tree.find("./{*}Price/{*}PriceAmount")
        if price_unit_node is None:
            return
        invoice_line.ubl_price_unit = float(price_unit_node.text)

    def _import_fill_invoice_line_form(
        self, journal, tree, invoice, invoice_line, qty_factor
    ):
        res = super()._import_fill_invoice_line_form(
            journal, tree, invoice, invoice_line, qty_factor
        )
        self._set_invoice_line_ubl_billed_quantity_and_unece_unit_code(
            tree, invoice_line
        )
        self._set_invoice_ubl_price_unit(tree, invoice_line)
        if not invoice_line.ubl_unece_unit_code:
            return res
        if not self._import_fill_invoice_line_packaging(invoice_line):
            self._import_fill_invoice_line_uom(invoice_line)
        return res

    def _import_fill_invoice_line_uom(self, invoice_line):
        uom_id = self.env["uom.uom"].get_uom_id_by_unece_code(
            invoice_line.ubl_unece_unit_code
        )
        if not uom_id:
            return False
        uom = self.env["uom.uom"].browse(uom_id)
        if (
            invoice_line.product_id
            and uom.category_id
            != invoice_line.product_id.product_tmpl_id.uom_id.category_id
        ):
            return False
        invoice_line.product_uom_id = uom
        invoice_line.price_unit = invoice_line.ubl_price_unit
        return True

    def _import_fill_invoice_line_packaging(self, invoice_line):
        # the unitCode attr is based on UNECE Rec 20 (UoM)
        # when Rec 21 (packaging) codes are used, they may be prefixed with "X"
        # we therefore check both formats (e.g. "8A" and "X8A")
        pl_model = self.env["product.packaging.level"]
        packaging_level_ids = pl_model.get_packaging_level_ids_for_codes(
            invoice_line.ubl_unece_unit_code,
            invoice_line.ubl_unece_unit_code.lstrip("X"),
        )
        if not packaging_level_ids:
            return False
        product_packaging = self.env["product.packaging"].search(
            [
                ("product_id", "=", invoice_line.product_id.id),
                ("packaging_level_id", "in", packaging_level_ids),
            ],
            limit=1,
        )
        if product_packaging:
            invoice_line.product_packaging_id = product_packaging
            invoice_line.product_packaging_qty = invoice_line.ubl_billed_quantity
            if product_packaging.qty > 0 and invoice_line.ubl_price_unit:
                invoice_line.price_unit = (
                    invoice_line.ubl_price_unit / product_packaging.qty
                )
            return True
        return False
