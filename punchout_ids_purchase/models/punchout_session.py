# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import date, datetime

from lxml import objectify
from lxml.etree import XMLSyntaxError

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _prepare_purchase_order_lines(self):
        """Prepare order lines from IDS shopping cart response."""
        self.ensure_one()
        if self.backend_id.protocol != "ids":
            return super()._prepare_purchase_order_lines()

        if not self.response:
            return []

        try:
            xml_data = self.response
            if isinstance(xml_data, str):
                xml_data = xml_data.encode("utf-8")
            order = objectify.fromstring(xml_data)
        except XMLSyntaxError as e:
            _logger.error("Error parsing IDS response: %s", e)
            return []

        lines = []
        if hasattr(order, "Order") and hasattr(order.Order, "OrderItem"):
            for order_item in order.Order.OrderItem:
                product = self._get_or_create_product_ids(order_item)
                line_vals = self._prepare_ids_order_line(product, order_item, order)
                if line_vals:
                    lines.append((0, 0, line_vals))

        return lines

    def _prepare_ids_order_line(self, product, order_item, order):
        """Prepare purchase order line values from IDS OrderItem."""
        self.ensure_one()

        # Get quantity and UoM
        quantity = float(order_item.Qty)
        uom = self._get_or_create_uom_ids(order_item)

        # Get price (NetPrice is for the full quantity)
        net_price = float(order_item.NetPrice)
        unit_price = net_price / quantity * uom.factor_inv if quantity else 0

        # Get description
        description = str(order_item.Kurztext)

        # Get delivery date if available
        date_planned = self._get_ids_delivery_date(order)

        return {
            "product_id": product.id,
            "name": description,
            "product_qty": quantity * uom.factor,
            "price_unit": unit_price,
            "product_uom": uom.id,
            "date_planned": date_planned,
            "taxes_id": [(6, 0, product.supplier_taxes_id.ids)],
        }

    def _get_ids_delivery_date(self, order):
        """Extract delivery date from IDS order."""
        if hasattr(order, "Order") and hasattr(order.Order, "OrderInfo"):
            order_info = order.Order.OrderInfo

            # Try DeliveryDate first
            if hasattr(order_info, "DeliveryDate"):
                date_str = str(order_info.DeliveryDate)[:10]
                if date_str:
                    try:
                        return fields.Date.from_string(date_str)
                    except ValueError:
                        _logger.debug("Invalid IDS DeliveryDate format: %s", date_str)

            # Try DeliveryWeek/DeliveryYear
            if hasattr(order_info, "DeliveryWeek") and hasattr(
                order_info, "DeliveryYear"
            ):
                try:
                    week = int(order_info.DeliveryWeek)
                    year = int(order_info.DeliveryYear)
                    # Get Friday of delivery week
                    return datetime.strptime(f"{year}/{week:02d}/5", "%Y/%W/%w").date()
                except (ValueError, TypeError):
                    _logger.debug(
                        "Invalid IDS DeliveryWeek/Year: %s/%s",
                        getattr(order_info, "DeliveryWeek", ""),
                        getattr(order_info, "DeliveryYear", ""),
                    )

        return date.today()

    def _get_or_create_product_ids(self, order_item):
        """Find existing product by supplier info or create a new one."""
        self.ensure_one()
        backend = self.backend_id
        Product = self.env["product.product"]

        art_no = str(order_item.ArtNo)
        ean = str(getattr(order_item, "EAN", "")) if hasattr(order_item, "EAN") else ""

        # Build search domain: match by supplier (partner + product code)
        # and/or by barcode. Crucially, do NOT fall back to "barcode is
        # empty" — that matched virtually every product in the database.
        seller_clause = (
            backend.partner_id
            and art_no
            and [
                "&",
                ("seller_ids.partner_id", "=", backend.partner_id.id),
                ("seller_ids.product_code", "=", art_no),
            ]
        )
        barcode_clause = ean and [("barcode", "=", ean)]
        if seller_clause and barcode_clause:
            domain = ["|", *seller_clause, *barcode_clause]
        else:
            domain = seller_clause or barcode_clause or None

        # Don't ``limit=1`` so we can warn about ambiguous matches
        # (same partner_id + supplier code attached to multiple
        # products — pathological data, but it happens when a backend
        # was reconfigured and old supplierinfo lines were never
        # cleaned up).
        matches = Product.search(domain) if domain else Product.browse()
        if len(matches) > 1:
            _logger.warning(
                "[punchout.ids.match] backend=%s art_no=%s matched %d "
                "products (%s); picking the first deterministically.",
                backend.name,
                art_no,
                len(matches),
                matches.mapped("display_name"),
            )
        if matches:
            product = matches[0]
            self._update_product_ids(product, order_item)
            return product

        # Create new product if auto_create_products is enabled
        if backend.auto_create_products:
            product_vals = self._parse_ids_order_item(order_item)
            product = Product.sudo().create(product_vals)
            self._post_create_product_hook(product, order_item)
            return product

        # Fallback: return a generic product
        return Product.search([("purchase_ok", "=", True)], limit=1)

    def _post_create_product_hook(self, product, raw_data):
        """Hook fired after a product is auto-created from a punchout
        cart. Empty in base — override in private/glue modules to
        enrich the product (image, dimensions, HS code, brand, etc.)
        from the supplier's REST API. ``raw_data`` is the protocol-
        specific cart-line element; for IDS it is the parsed
        ``OrderItem`` lxml objectify element so overrides can pull
        IDS-specific fields (ArtNo, EAN, Langtext, etc.) without
        re-parsing.

        Hook fires once per newly-created product, never on existing
        product matches. Failures inside the hook MUST be caught by
        the override — the cart-import flow should never break
        because an enrichment call timed out."""

    def _parse_ids_order_item(self, order_item):
        """Parse IDS OrderItem to product creation values."""
        self.ensure_one()
        backend = self.backend_id

        description = str(order_item.Kurztext)
        art_no = str(order_item.ArtNo)
        ean = str(getattr(order_item, "EAN", "")) if hasattr(order_item, "EAN") else ""
        long_text = (
            str(getattr(order_item, "Langtext", ""))
            if hasattr(order_item, "Langtext")
            else ""
        )

        # Get UoM
        uom = self._get_or_create_uom_ids(order_item)
        reference_uom = self.env["uom.uom"].search(
            [("category_id", "=", uom.category_id.id), ("uom_type", "=", "reference")],
            limit=1,
        )

        # Calculate unit price
        quantity = float(order_item.Qty)
        net_price = float(order_item.NetPrice)
        unit_price = net_price / quantity * uom.factor_inv if quantity else 0

        # Get VAT rate and find matching tax
        vat_rate = float(getattr(order_item, "VAT", 0))
        company = backend._get_company()
        purchase_tax = self.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("amount", "=", vat_rate),
                ("price_include", "=", False),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        if not purchase_tax:
            purchase_tax = company.account_purchase_tax_id

        # Get currency
        currency = self.env["res.currency"].search(
            [("name", "=", str(order_item.getparent().OrderInfo.Cur))], limit=1
        )
        if not currency:
            currency = company.currency_id

        product_vals = {
            "name": description,
            "type": "consu",
            "purchase_ok": True,
            "description_purchase": long_text if long_text else None,
            "uom_id": reference_uom.id if reference_uom else uom.id,
            "uom_po_id": uom.id,
        }

        if ean:
            product_vals["barcode"] = ean

        # Add category if configured
        if backend.product_category_id:
            product_vals["categ_id"] = backend.product_category_id.id

        # Add taxes
        if purchase_tax:
            product_vals["supplier_taxes_id"] = [(6, 0, purchase_tax.ids)]

        # Add supplier info
        if backend.partner_id:
            product_vals["seller_ids"] = [
                (
                    0,
                    0,
                    {
                        "partner_id": backend.partner_id.id,
                        "product_code": art_no,
                        "product_name": description,
                        "price": unit_price,
                        "min_qty": 0,
                        "currency_id": currency.id,
                    },
                )
            ]

        return product_vals

    def _update_product_ids(self, product, order_item):
        """Update existing product supplier info from IDS OrderItem."""
        self.ensure_one()
        backend = self.backend_id

        art_no = str(order_item.ArtNo)
        description = str(order_item.Kurztext)
        quantity = float(order_item.Qty)
        net_price = float(order_item.NetPrice)

        uom = self._get_or_create_uom_ids(order_item)
        unit_price = net_price / quantity * uom.factor_inv if quantity else 0

        # Get currency
        currency = self.env["res.currency"].search(
            [("name", "=", str(order_item.getparent().OrderInfo.Cur))], limit=1
        )
        if not currency:
            currency = backend._get_company().currency_id

        # Find matching seller
        matching_seller = None
        for seller in product.seller_ids:
            if (
                seller.partner_id == backend.partner_id
                and seller.product_code == art_no
                and seller.currency_id == currency
            ):
                matching_seller = seller
                break

        if matching_seller:
            matching_seller.sudo().price = unit_price
        else:
            product.sudo().write(
                {
                    "seller_ids": [
                        (
                            0,
                            0,
                            {
                                "partner_id": backend.partner_id.id,
                                "product_code": art_no,
                                "product_name": description,
                                "price": unit_price,
                                "min_qty": 0,
                                "currency_id": currency.id,
                            },
                        )
                    ]
                }
            )

    def _get_or_create_uom_ids(self, order_item):
        """Get or create UoM based on IDS QU (quantity unit) and PriceBasis."""
        self.ensure_one()

        qu_code = str(order_item.QU) if hasattr(order_item, "QU") else ""
        price_basis = float(getattr(order_item, "PriceBasis", 1))

        uom = None
        if qu_code:
            uom = self.env["punchout.uom.mapping"]._get_uom_by_supplier_code(
                self.backend_id, qu_code
            )

        if not uom:
            uom = self.env.ref("uom.product_uom_unit")

        # Handle price basis (e.g., price per 100 units)
        if price_basis != 1:
            # Look for existing UoM with matching factor
            factor = 1 / price_basis
            existing_uom = self.env["uom.uom"].search(
                [
                    ("category_id", "=", uom.category_id.id),
                    ("factor", "=", factor),
                ],
                limit=1,
            )
            if existing_uom:
                return existing_uom

            # Create new UoM for price basis
            uom_type = "bigger" if price_basis > 1 else "smaller"
            new_uom = (
                self.env["uom.uom"]
                .sudo()
                .create(
                    {
                        "name": f"{int(price_basis)} {uom.name}",
                        "category_id": uom.category_id.id,
                        "factor": factor,
                        "uom_type": uom_type,
                    }
                )
            )
            return new_uom

        return uom
