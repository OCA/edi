# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import date

import lxml.etree as ET

from odoo import models

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _prepare_purchase_order_lines(self):
        """Prepare order lines from cXML PunchOutOrderMessage response."""
        self.ensure_one()
        if self.backend_id.protocol != "cxml":
            return super()._prepare_purchase_order_lines()

        if not self.response:
            return []

        lines = []
        try:
            tree = ET.fromstring(self.response.encode())
            for item in tree.findall(".//ItemIn"):
                line_vals = self._parse_cxml_item(item)
                if line_vals:
                    lines.append((0, 0, line_vals))
        except ET.XMLSyntaxError as e:
            _logger.error("Error parsing cXML response: %s", e)
            return []

        return lines

    def _parse_cxml_item(self, item_element):
        """Parse a cXML ItemIn element and return purchase order line values."""
        self.ensure_one()

        # Get quantity
        quantity = float(item_element.get("quantity", 1))

        # Get ItemDetail
        item_detail = item_element.find("ItemDetail")
        if item_detail is None:
            return {}

        # Get description
        description_elem = item_detail.find("Description")
        description = (
            description_elem.text if description_elem is not None else "Unknown"
        )

        # Get unit price
        unit_price_elem = item_detail.find("UnitPrice/Money")
        unit_price = 0.0
        if unit_price_elem is not None and unit_price_elem.text:
            try:
                unit_price = float(unit_price_elem.text)
            except (ValueError, TypeError):
                _logger.debug("Invalid cXML UnitPrice format: %s", unit_price_elem.text)

        # Get supplier part ID
        item_id = item_element.find("ItemID")
        supplier_part_id = ""
        if item_id is not None:
            supplier_part_elem = item_id.find("SupplierPartID")
            if supplier_part_elem is not None:
                supplier_part_id = supplier_part_elem.text or ""

        # Get or create product
        product = self._get_or_create_product_cxml(
            supplier_part_id, description, unit_price, item_detail
        )

        # Get UoM
        uom = self._get_uom_for_cxml_item(item_detail)

        return {
            "product_id": product.id,
            "name": description,
            "product_qty": quantity,
            "price_unit": unit_price,
            "product_uom": uom.id,
            "date_planned": date.today(),
        }

    def _get_or_create_product_cxml(
        self, supplier_part_id, description, unit_price, item_detail
    ):
        """Find existing product by supplier info or create a new one."""
        self.ensure_one()
        backend = self.backend_id
        Product = self.env["product.product"]

        # Try to find by supplier product code. Don't ``limit=1`` so
        # we can warn about ambiguous matches (same partner_id +
        # supplier-part attached to multiple products — pathological
        # data, but it happens when a backend was reconfigured and
        # old supplierinfo lines were never cleaned up).
        if supplier_part_id and backend.partner_id:
            matches = Product.search(
                [
                    ("seller_ids.partner_id", "=", backend.partner_id.id),
                    ("seller_ids.product_code", "=", supplier_part_id),
                ]
            )
            if len(matches) > 1:
                _logger.warning(
                    "[punchout.cxml.match] backend=%s supplier_part=%s matched "
                    "%d products (%s); picking the first deterministically.",
                    backend.name,
                    supplier_part_id,
                    len(matches),
                    matches.mapped("display_name"),
                )
            if matches:
                return matches[0]

        # Create new product if auto_create_products is enabled
        if backend.auto_create_products:
            uom = self._get_uom_for_cxml_item(item_detail)
            product_vals = {
                "name": description,
                "type": "consu",
                "purchase_ok": True,
                "uom_id": uom.id,
                "uom_po_id": uom.id,
            }

            # Add category if configured
            if backend.product_category_id:
                product_vals["categ_id"] = backend.product_category_id.id

            # Add supplier info
            if backend.partner_id:
                # cXML's UnitPrice/Money carries the ISO currency in
                # the @currency attribute. product.supplierinfo.currency_id
                # is NOT NULL since Odoo 18, so we MUST resolve a record.
                # Fall back to the company currency when the cart's code
                # is unknown / absent so we never trip the constraint.
                money_elem = item_detail.find("UnitPrice/Money")
                currency_code = (
                    money_elem.get("currency", "") if money_elem is not None else ""
                )
                currency = (
                    self.env["res.currency"].search(
                        [("name", "=", currency_code)], limit=1
                    )
                    if currency_code
                    else self.env["res.currency"]
                )
                if not currency:
                    currency = backend._get_company().currency_id
                product_vals["seller_ids"] = [
                    (
                        0,
                        0,
                        {
                            "partner_id": backend.partner_id.id,
                            "product_code": supplier_part_id,
                            "product_name": description,
                            "price": unit_price,
                            "currency_id": currency.id,
                        },
                    )
                ]

            product = Product.sudo().create(product_vals)
            self._post_create_product_hook(
                product,
                {
                    "supplier_part_id": supplier_part_id,
                    "description": description,
                    "unit_price": unit_price,
                    "item_detail": item_detail,
                },
            )
            return product

        # Fallback: return a generic product or raise error
        return Product.search([("purchase_ok", "=", True)], limit=1)

    def _post_create_product_hook(self, product, raw_data):
        """Hook fired after a product is auto-created from a punchout
        cart. Empty in base — override in private/glue modules to
        enrich the product (image, dimensions, HS code, brand, etc.)
        from the supplier's REST API. ``raw_data`` is the protocol-
        specific cart-line dict; for cXML it carries
        ``supplier_part_id``, ``description``, ``unit_price`` and the
        raw ``item_detail`` lxml element so overrides can pull
        protocol-specific fields without re-parsing.

        Hook fires once per newly-created product, never on existing
        product matches. Failures inside the hook MUST be caught by
        the override — the cart-import flow should never break
        because an enrichment call timed out."""

    def _get_uom_for_cxml_item(self, item_detail):
        """Get UoM for cXML item, using the full punchout.uom.mapping chain."""
        self.ensure_one()
        uom_elem = item_detail.find("UnitOfMeasure")
        uom_code = uom_elem.text if uom_elem is not None else None
        if uom_code:
            uom = self.env["punchout.uom.mapping"]._get_uom_by_supplier_code(
                self.backend_id, uom_code
            )
            if uom:
                return uom
        return self.env.ref("uom.product_uom_unit")
