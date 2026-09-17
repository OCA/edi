# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import date, timedelta

from odoo import models

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _prepare_purchase_order_lines(self):
        """Prepare order lines from OCI shopping cart response."""
        self.ensure_one()
        if self.backend_id.protocol != "oci":
            return super()._prepare_purchase_order_lines()

        if not self.response:
            return []

        try:
            form_data = json.loads(self.response)
        except (json.JSONDecodeError, TypeError):
            _logger.error("Error parsing OCI response as JSON")
            return []

        # Parse OCI form data into product dictionaries
        product_dicts = self._parse_oci_form_data(form_data)

        lines = []
        for product_dict in product_dicts:
            product = self._get_or_create_product_oci(product_dict)
            line_vals = self._prepare_oci_order_line(product, product_dict)
            if line_vals:
                lines.append((0, 0, line_vals))

        return lines

    def _parse_oci_form_data(self, form_data):
        """Parse OCI form data (NEW_ITEM-KEY[index]) into list of dicts.

        OCI sends cart items as form fields like:
        NEW_ITEM-DESCRIPTION[1]=Product Name
        NEW_ITEM-QUANTITY[1]=10
        NEW_ITEM-PRICE[1]=99.99
        """
        prefix = "NEW_ITEM-"

        # Find all unique keys (without prefix and index)
        product_keys = set()
        for key in form_data:
            if key.startswith(prefix) and "[" in key and key.endswith("]"):
                # Extract key name between prefix and [index]
                key_name = key[len(prefix) : key.index("[")]
                product_keys.add(key_name)

        # Parse items by index
        product_dicts = []
        index = 1
        while True:
            # Check if any key exists for this index
            has_item = any(
                f"{prefix}{key}[{index}]" in form_data for key in product_keys
            )
            if not has_item:
                break

            product_dict = {}
            for key in product_keys:
                form_key = f"{prefix}{key}[{index}]"
                if form_key in form_data:
                    value = form_data[form_key]
                    # Handle lists (e.g., from multi-value fields)
                    if isinstance(value, list):
                        value = value[0] if value else ""
                    product_dict[key] = value

            # Also check for LONGTEXT with different format
            longtext_key = f"NEW_ITEM-LONGTEXT_{index}:132[]"
            if longtext_key in form_data:
                value = form_data[longtext_key]
                if isinstance(value, list):
                    value = value[0] if value else ""
                product_dict["LONGTEXT"] = value

            if product_dict:
                product_dicts.append(product_dict)
            index += 1

        return product_dicts

    def _prepare_oci_order_line(self, product, product_dict):
        """Prepare purchase order line values from OCI product dict."""
        self.ensure_one()

        # Get quantity
        quantity = float(product_dict.get("QUANTITY", 1))

        # Get unit price
        price = float(product_dict.get("PRICE", 0))

        # Get description
        description = product_dict.get("DESCRIPTION", product.name)

        # Get lead time for date_planned
        leadtime = float(product_dict.get("LEADTIME", 0))
        date_planned = date.today() + timedelta(days=leadtime)

        # Get UoM
        uom = self._get_uom_for_oci_item(product_dict)

        return {
            "product_id": product.id,
            "name": description,
            "product_qty": quantity,
            "price_unit": price,
            "product_uom": uom.id,
            "date_planned": date_planned,
        }

    def _get_or_create_product_oci(self, product_dict):
        """Find existing product by supplier info or create a new one."""
        self.ensure_one()
        backend = self.backend_id
        Product = self.env["product.product"]

        vendor_mat = product_dict.get("VENDORMAT", "")
        description = product_dict.get("DESCRIPTION", "Unknown Product")

        # Try to find by supplier product code. Don't ``limit=1`` so
        # we can warn about ambiguous matches (same partner_id +
        # vendor code attached to multiple products — pathological
        # data, but it happens when a backend was reconfigured and
        # old supplierinfo lines were never cleaned up).
        if vendor_mat and backend.partner_id:
            matches = Product.search(
                [
                    ("seller_ids.partner_id", "=", backend.partner_id.id),
                    ("seller_ids.product_code", "=", vendor_mat),
                ]
            )
            if len(matches) > 1:
                _logger.warning(
                    "[punchout.oci.match] backend=%s vendor_code=%s matched "
                    "%d products (%s); picking the first deterministically.",
                    backend.name,
                    vendor_mat,
                    len(matches),
                    matches.mapped("display_name"),
                )
            if matches:
                return matches[0]

        # Create new product if auto_create_products is enabled
        if backend.auto_create_products:
            uom = self._get_uom_for_oci_item(product_dict)
            # Backend-driven defaults (type, is_storable, tracking,
            # categ_id) — see
            # ``punchout.backend._get_auto_create_product_defaults``.
            # Replaces the previously hardcoded ``type="consu"`` so
            # spare-parts vendors can default to storable inventory
            # in one config knob.
            product_vals = {
                "name": description,
                "uom_id": uom.id,
                "uom_po_id": uom.id,
                **backend._get_auto_create_product_defaults(),
            }

            # Add long description if different from main description
            longtext = product_dict.get("LONGTEXT", "")
            if longtext and longtext != description:
                product_vals["description_purchase"] = longtext

            # Add supplier info
            if backend.partner_id:
                price = float(product_dict.get("PRICE", 0))
                leadtime = int(float(product_dict.get("LEADTIME", 0)))
                # OCI's NEW_ITEM-CURRENCY[n] is an ISO code (TVH sends "EUR").
                # product.supplierinfo.currency_id is NOT NULL since
                # Odoo 18, so we MUST resolve a record. Fall back to
                # the company currency when the cart's code is unknown
                # (or absent) so we never trip the constraint.
                currency_code = product_dict.get("CURRENCY", "")
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
                            "product_code": vendor_mat,
                            "product_name": description,
                            "price": price,
                            "delay": leadtime,
                            "currency_id": currency.id,
                        },
                    )
                ]

            product = Product.sudo().create(product_vals)
            self._post_create_product_hook(product, product_dict)
            return product

        # Fallback: return a generic product
        return Product.search([("purchase_ok", "=", True)], limit=1)

    def _post_create_product_hook(self, product, raw_data):
        """Hook fired after a product is auto-created from a punchout
        cart. Empty in base — override in private/glue modules to
        enrich the product (image, dimensions, HS code, brand, etc.)
        from the supplier's REST API. ``raw_data`` is the protocol-
        specific cart-line dict (OCI ``NEW_ITEM-*`` form data here)
        so overrides can pull supplier-specific keys (e.g. VENDORMAT)
        without re-parsing the whole cart.

        Hook fires once per newly-created product, never on existing
        product matches. Failures inside the hook MUST be caught by
        the override — the cart-import flow should never break
        because an enrichment call timed out."""

    def _get_uom_for_oci_item(self, product_dict):
        """Get UoM for OCI item, using the full punchout.uom.mapping chain."""
        self.ensure_one()
        uom_code = product_dict.get("UNIT", "")
        if uom_code:
            uom = self.env["punchout.uom.mapping"]._get_uom_by_supplier_code(
                self.backend_id, uom_code
            )
            if uom:
                return uom
        return self.env.ref("uom.product_uom_unit")
