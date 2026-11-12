# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "edi.exchange.consumer.mixin"]

    x_sps_location = fields.Char(
        "SPS location ID",
        help="Trading-partner location identifier from the RSX address "
        "block (AddressLocationNumber).",
    )
    x_sps_customer_ref = fields.Char(
        "SPS customer reference",
        help="Customer reference sent by the trading partner "
        "(OrderHeader.CustomerOrderNumber).",
    )
    x_sps_dropship = fields.Boolean(
        "SPS dropship",
        help="Set when the RSX Meta.IsDropShip flag marks the order as a "
        "dropshipment (ship-to differs from the buying party).",
    )
    x_sps_ack_type = fields.Char(
        "SPS acknowledgement type",
        help="Latest OrderAck AcknowledgementType received for this order "
        "(X12 855 codes: BA accepted, AB accepted with changes, "
        "RB rejected...).",
    )
    x_sps_ack_number = fields.Char("SPS acknowledgement number")
    x_sps_ack_date = fields.Date("SPS acknowledgement date")

    def _edi_sps_import_order(self, order):
        """Create a draft sale.order from a parsed RSX <Order> dict.

        RSX element names are kept verbatim by the codec, so the reads
        below match the SPS documentation (Header/OrderHeader/...).
        """
        order_header = (order.get("Header") or {}).get("OrderHeader") or {}
        po_number = order_header.get("PurchaseOrderNumber")
        if not po_number:
            raise UserError(self.env._("Order has no PurchaseOrderNumber."))
        purpose = order_header.get("TsetPurposeCode") or "00"
        if purpose not in ("00", "01", "05", "06", "07"):
            raise UserError(self.env._("Unsupported TsetPurposeCode '%s'.", purpose))
        meta = order.get("Meta") or {}
        partner = self._edi_sps_find_partner(
            order_header.get("TradingPartnerId"),
            meta.get("InterchangeSenderID"),
            meta.get("SenderUniqueID"),
        )
        if not partner:
            raise UserError(
                self.env._(
                    "No partner found for trading partner '%s'. "
                    "Set the customer's Internal Reference to the SPS "
                    "trading partner id.",
                    order_header.get("TradingPartnerId"),
                )
            )
        existing = self.search(
            [
                ("partner_id", "=", partner.id),
                ("client_order_ref", "=", po_number),
            ],
            limit=1,
        )
        # RSX TsetPurposeCode: 00 original, 01 cancellation,
        # 05 replace, 06 confirmation, 07 duplicate.
        if purpose == "01":
            if not existing:
                raise UserError(
                    self.env._(
                        "Cancellation for PO %(po)s / %(partner)s: "
                        "no matching sale order found.",
                        po=po_number,
                        partner=partner.name,
                    )
                )
            existing.action_cancel()
            return existing
        if purpose in ("06", "07"):
            # Confirmation/duplicate transmissions carry no changes.
            if not existing:
                raise UserError(
                    self.env._(
                        "TsetPurposeCode '%(purpose)s' for PO %(po)s / "
                        "%(partner)s: no matching sale order found.",
                        purpose=purpose,
                        po=po_number,
                        partner=partner.name,
                    )
                )
            return existing
        if purpose == "05":
            # Replace: cancel the live order if there is one, then import
            # the replacement as a new draft (also covers re-sending a
            # replace after the original was already cancelled).
            if existing and existing.state not in ("done", "cancel"):
                existing.action_cancel()
        elif existing:
            raise UserError(
                self.env._(
                    "Sale order %(order)s already exists for PO %(po)s / %(partner)s.",
                    order=existing.name,
                    po=po_number,
                    partner=partner.name,
                )
            )
        return self.create(self._edi_sps_order_values(order, partner))

    def _edi_sps_apply_ack(self, order_ack):
        """Record an RSX <OrderAck> header on the matching sale order.

        Returns the sale order, or an empty recordset when no order
        matches the acknowledgement's PO/partner pair.
        """
        order_header = (order_ack.get("Header") or {}).get("OrderHeader") or {}
        po_number = order_header.get("PurchaseOrderNumber")
        if not po_number:
            return self.browse()
        partner = self._edi_sps_find_partner(order_header.get("TradingPartnerId"))
        if not partner:
            return self.browse()
        order = self.search(
            [
                ("partner_id", "=", partner.id),
                ("client_order_ref", "=", po_number),
            ],
            limit=1,
        )
        if not order:
            return self.browse()
        order.write(
            {
                "x_sps_ack_type": order_header.get("AcknowledgementType"),
                "x_sps_ack_number": order_header.get("AcknowledgementNumber"),
                "x_sps_ack_date": order_header.get("AcknowledgementDate") or False,
            }
        )
        return order

    def _edi_sps_order_values(self, order, partner):
        header = order.get("Header") or {}
        order_header = header.get("OrderHeader") or {}
        commitment_date = next(
            (
                d["Date"]
                for d in header.get("Dates") or []
                if d.get("DateTimeQualifier") == "002" and d.get("Date")
            ),
            None,
        )
        order_lines = []
        for line_item in order.get("LineItem") or []:
            line = line_item.get("OrderLine") or {}
            product = self._edi_sps_find_product(line, partner)
            if not product:
                raise UserError(
                    self.env._(
                        "No product found for item ids %(line)s on line %(seq)s.",
                        line=line,
                        seq=line.get("LineSequenceNumber"),
                    )
                )
            order_lines.append(
                Command.create(
                    {
                        "product_id": product.id,
                        "product_uom_id": self._edi_sps_uom(
                            line.get("OrderQtyUOM"), product
                        ).id,
                        "product_uom_qty": self._edi_sps_to_float(line.get("OrderQty")),
                        "price_unit": self._edi_sps_to_float(line.get("PurchasePrice")),
                        "x_sps_line_ref": self._edi_sps_line_ref(line),
                    }
                )
            )
        if not order_lines:
            raise UserError(
                self.env._(
                    "Order %s has no order lines.",
                    order_header.get("PurchaseOrderNumber"),
                )
            )
        return {
            "partner_id": partner.id,
            "client_order_ref": order_header.get("PurchaseOrderNumber"),
            "date_order": order_header.get("PurchaseOrderDate")
            or fields.Datetime.now(),
            "commitment_date": commitment_date,
            "order_line": order_lines,
            "x_sps_location": self._edi_sps_location(order),
            "x_sps_customer_ref": order_header.get("CustomerOrderNumber"),
            "x_sps_dropship": str(
                (order.get("Meta") or {}).get("IsDropShip") or ""
            ).lower()
            in ("true", "1"),
            "currency_id": self._edi_sps_currency(order_header),
            "note": self._edi_sps_notes(order, header),
            "partner_shipping_id": self._edi_sps_ship_to(order, partner).id,
            "payment_term_id": self._edi_sps_payment_term(header),
            # TODO: dropship customer refs — see
            # docs/EDI_SPSCOMMERCE.md mapping tables.
        }

    def _edi_sps_find_partner(self, *refs):
        """Find res.partner by SPS trading partner id or Internal Reference."""
        for ref in refs:
            if ref:
                partner = self.env["res.partner"].search(
                    [
                        "|",
                        ("x_sps_trading_partner_id", "=", str(ref).strip()),
                        ("ref", "=", str(ref).strip()),
                    ],
                    limit=1,
                )
                if partner:
                    return partner
        return self.env["res.partner"]

    def _edi_sps_find_product(self, order_line, partner):
        """Find product.product via the RSX part-number match chain.

        ``order_line`` is the raw <OrderLine> dict — it doubles as the
        item-id block. Priority (design doc): VendorPartNumber/
        ApplicationId -> default_code; BuyerPartNumber ->
        product.customer.code; GTIN/EAN/ConsumerPackageCode -> barcode.
        """
        Product = self.env["product.product"]
        for key in ("VendorPartNumber", "ApplicationId"):
            code = (order_line.get(key) or "").strip()
            if code:
                product = Product.search([("default_code", "=", code)], limit=1)
                if product:
                    return product
        buyer_code = (order_line.get("BuyerPartNumber") or "").strip()
        if buyer_code and self.env.registry.get("product.customer.code"):
            customer_code = self.env["product.customer.code"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("product_code", "=", buyer_code),
                ],
                limit=1,
            )
            if customer_code and "product_id" in customer_code._fields:
                return customer_code.product_id
        for key in ("GTIN", "EAN", "ConsumerPackageCode"):
            code = (order_line.get(key) or "").strip()
            if code:
                product = Product.search([("barcode", "=", code)], limit=1)
                if product:
                    return product
        return Product

    @staticmethod
    def _edi_sps_location(order):
        """First non-empty AddressLocationNumber across the order's addresses."""
        addresses = order.get("Address") or []
        if isinstance(addresses, dict):
            addresses = [addresses]
        for address in addresses:
            location = (address.get("AddressLocationNumber") or "").strip()
            if location:
                return location
        return False

    @staticmethod
    def _edi_sps_line_ref(order_line):
        """First ReferenceID of the line's References block, if any."""
        references = order_line.get("References") or []
        if isinstance(references, dict):
            references = [references]
        for reference in references:
            ref_id = (reference.get("ReferenceID") or "").strip()
            if ref_id:
                return ref_id
        return False

    def _edi_sps_currency(self, order_header):
        """Order currency from BuyersCurrency/SellersCurrency ISO codes."""
        Currency = self.env["res.currency"]
        for key in ("BuyersCurrency", "SellersCurrency"):
            code = (order_header.get(key) or "").strip().upper()
            if code:
                currency = Currency.search([("name", "=", code)], limit=1)
                if currency:
                    return currency.id
        return False

    @staticmethod
    def _edi_sps_notes(order, header):
        """Join the free-text Notes blocks into the order's note field."""
        notes = order.get("Notes") or header.get("Notes") or []
        if isinstance(notes, dict):
            notes = [notes]
        texts = [(n.get("Note") or "").strip() for n in notes]
        return "\n".join(t for t in texts if t) or False

    def _edi_sps_ship_to(self, order, partner):
        """Find or create the delivery child partner from Address[ST]."""
        addresses = order.get("Address") or []
        if isinstance(addresses, dict):
            addresses = [addresses]
        ship_to = next((a for a in addresses if a.get("AddressTypeCode") == "ST"), None)
        if not ship_to:
            # partner_shipping_id is required on sale.order; without an
            # explicit ship-to address the customer is the delivery party.
            return partner
        country = self.env["res.country"]
        if ship_to.get("Country"):
            country = (
                country.search(
                    [("code", "=", ship_to["Country"].strip().upper())], limit=1
                )
                or country
            )
        state = self.env["res.country.state"]
        if ship_to.get("State") and country:
            state = state.search(
                [
                    ("code", "=", ship_to["State"].strip().upper()),
                    ("country_id", "=", country.id),
                ],
                limit=1,
            )
        vals = {
            "name": (ship_to.get("AddressName") or "").strip()
            or f"{partner.name} - SPS",
            "street": ship_to.get("Address1") or False,
            "street2": "\n".join(
                p
                for p in (
                    ship_to.get("Address2"),
                    ship_to.get("Address3"),
                    ship_to.get("Address4"),
                )
                if p
            )
            or False,
            "city": ship_to.get("City") or False,
            "zip": ship_to.get("PostalCode") or False,
            "country_id": country.id or False,
            "state_id": state.id or False,
            "parent_id": partner.id,
            "type": "delivery",
        }
        gln = (ship_to.get("AddressLocationNumber") or "").strip()
        children = partner.child_ids.filtered(lambda c: c.type == "delivery")
        # GLN match wins: the same location id always resolves to the
        # same delivery address even if street formatting drifts.
        if gln:
            by_gln = children.filtered(lambda c: c.x_sps_location == gln)
            if by_gln:
                return by_gln[:1]
        existing = children.filtered(
            lambda c: c.street == vals["street"]
            and c.city == vals["city"]
            and c.zip == vals["zip"]
        )
        if existing:
            if gln and not existing[:1].x_sps_location:
                existing[:1].x_sps_location = gln
            return existing[:1]
        vals["x_sps_location"] = gln or False
        return self.env["res.partner"].create(vals)

    def _edi_sps_payment_term(self, header):
        """Resolve RSX PaymentTerms to an account.payment.term.

        Matches on ``TermsNetDueDays`` via ``edi.sps.payment.term.map``;
        returns False (partner default applies) when unmapped.
        """
        terms = header.get("PaymentTerms") or []
        if isinstance(terms, dict):
            terms = [terms]
        days = next(
            (
                int(float(t["TermsNetDueDays"]))
                for t in terms
                if t.get("TermsNetDueDays")
            ),
            None,
        )
        if days is None:
            return False
        mapping = self.env["edi.sps.payment.term.map"].search(
            [("net_days", "=", days)], limit=1
        )
        return mapping.payment_term_id.id or False

    def _edi_sps_uom(self, code, product):
        """Resolve an X12 355 UOM code to a ``uom.uom`` for the order line.

        Falls back to the product's UoM when the code is unmapped or not
        convertible with it (Odoo requires a common reference UoM).
        """
        code = (code or "").strip()
        if code:
            uom_map = self.env["edi.sps.uom.map"].search([("code", "=", code)], limit=1)
            if uom_map and uom_map.uom_id._has_common_reference(product.uom_id):
                return uom_map.uom_id
        return product.uom_id

    @staticmethod
    def _edi_sps_to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
