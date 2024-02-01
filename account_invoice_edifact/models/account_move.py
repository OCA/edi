# Copyright 2023 Camtocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def edifact_invoice_generate_data(self):
        self.ensure_one()
        edifact_model = self.env["base.edifact"]
        lines = []
        interchange = self._edifact_invoice_get_interchange()

        header = self._edifact_invoice_get_header()
        product, vals = self._edifact_invoice_get_product()
        summary = self._edifact_invoice_get_summary(vals)
        lines += header + product + summary
        for segment in lines:
            interchange.add_segment(edifact_model.create_segment(*segment))
        return interchange.serialize()

    def _edifact_invoice_get_interchange(self):
        id_number = self.env["res.partner.id_number"]
        sender = id_number.search(
            [("partner_id", "=", self.invoice_user_id.partner_id.id)], limit=1
        )
        recipient = id_number.search([("partner_id", "=", self.partner_id.id)], limit=1)
        if not sender or not recipient:
            raise UserError(_("Partner is not allowed to use the feature."))
        sender_edifact = [sender.name, "14"]
        recipient_edifact = [recipient.name, "14"]
        syntax_identifier = ["UNOC", "3"]

        return self.env["base.edifact"].create_interchange(
            sender_edifact, recipient_edifact, self.id, syntax_identifier
        )

    def _edifact_invoice_get_address(self, partner):
        # We apply the same logic as:
        # https://github.com/OCA/edi/blob/
        # c41829a8d986c6751c07299807c808d15adbf4db/base_ubl/models/ubl.py#L39

        # oca/partner-contact/partner_address_street3 is installed
        if hasattr(partner, "street3"):
            return partner.street3 or partner.street2 or partner.street
        else:
            return partner.street2 or partner.street

    def _edifact_invoice_get_buyer(self):
        buyer = self.partner_id
        street = self._edifact_invoice_get_address(buyer)
        return [
            # Invoice information
            (
                "NAD",
                "IV",
                [buyer.id, "", "92"],
                "",
                buyer.commercial_company_name,
                [street, ""],
                buyer.city,
                "",
                buyer.zip,
                buyer.country_id.code,
            ),
            # Internal customer number
            ("RFF", ["IT", buyer.id]),
            # Buyer information
            (
                "NAD",
                "BY",
                [buyer.id, "", "92"],
                "",
                buyer.commercial_company_name,
                [buyer.street, ""],
                buyer.city,
                "",
                buyer.zip,
                buyer.country_id.code,
            ),
            ("RFF", ["API", ""]),
        ]

    def _edifact_invoice_get_seller(self):
        id_number = self.env["res.partner.id_number"]
        seller = self.invoice_user_id.partner_id
        seller_id_number = id_number.search([("partner_id", "=", seller.id)], limit=1)
        street = self._edifact_invoice_get_address(seller)
        return [
            # Seller information
            (
                "NAD",
                "SE",
                [seller_id_number.name, "", "92"],
                "",
                seller.commercial_company_name,
                [street, ""],
                seller.city,
                "",
                seller.zip,
                seller.country_id.code,
            ),
            # VAT registration number
            ("RFF", ["VA", seller.vat]),
            # Government reference number
            ("RFF", ["GN", seller.vat]),  # TODO: Fix it
        ]

    def _edifact_invoice_get_shipper(self):
        id_number = self.env["res.partner.id_number"]
        shipper = self.partner_shipping_id
        shipper_id_number = id_number.search([("partner_id", "=", shipper.id)], limit=1)
        return [
            # Delivery party Information
            (
                "NAD",
                "DP",
                [shipper_id_number.name, "", "92"],
                "",
                shipper.commercial_company_name,
                [shipper.street, ""],
                shipper.city,
                "",
                shipper.zip,
                shipper.country_id.code,
            ),
            ("RFF", ["API", ""]),
        ]

    def _edifact_invoice_get_header(self):
        source_orders = self.line_ids.sale_line_ids.order_id
        today = datetime.now().date().strftime("%Y%m%d")
        buyer = self.partner_id

        term_lines = self.invoice_payment_term_id.line_ids
        discount_percentage, discount_days = (
            term_lines.discount_percentage,
            term_lines.discount_days if len(term_lines) == 1 else 0,
        )

        header = [
            ("UNH", "1", ["INVOIC", "D", "96A", "UN", "EAN008"]),
            # Commercial invoice
            ("BGM", ["380", "", "", "Invoice"], self.payment_reference, "9"),
            # 35: Delivery date/time, actual
            (
                "DTM",
                [
                    "35",
                    max(
                        (
                            picking.date_done.date().strftime("%Y%m%d")
                            for order in source_orders
                            for picking in order.picking_ids
                            if picking.date_done
                        ),
                        default="",
                    ),
                    "102",
                ],
            ),
            # 11: Despatch date and/or time
            (
                "DTM",
                [
                    "11",
                    min(
                        (
                            order.commitment_date.date().strftime("%Y%m%d")
                            for order in source_orders
                            if order.commitment_date
                        ),
                        default="",
                    ),
                    "102",
                ],
            ),
            # Document/message date/time
            ("DTM", ["137", today, "102"]),
            ("PAI", ["", "", "42"]),
            # Regulatory information
            ("FTX", "REG", "", "", ""),
            # Payment detail/remittance information
            ("FTX", "PMD", "", "", ""),
            # Terms of payments
            ("FTX", "AAB", "", "", "30 jours net"),
            # Delivery note number
            ("RFF", ["DQ", self.id]),
            # Reference date/time
            # TODO: fixed value for now, to be clarified
            ("DTM", ["171", "99991231", "102"]),
            # Reference currency
            ("CUX", ["2", buyer.currency_id.name, "4"]),
            # Rate of exchange
            ("DTM", ["134", today, "102"]),
            ("PAT", "3"),
            # Terms net due date
            ("DTM", ["13", self.invoice_date_due, "102"]),
            # Discount terms
            (
                "PAT",
                "22",
                "",
                ["5", "3", "D", discount_days],
            ),
            # Discount percentage
            (
                "PCD",
                "12",
                discount_percentage,
                "13",
            ),
            # Penalty terms
            # ("PAT", "20"),  # TODO: check value this again later
            # Penalty percentage
            # ("PCD", "15", "0"),  # TODO: check value this again later
            # Allowance percentage
            # ("PCD", "1", "0", "13"),  # TODO: check value this again later
            # Allowance or charge amount
            # ("MOA", "8", "0"),  # TODO: check value this again later
        ]
        header = (
            header[:11]
            + self._edifact_invoice_get_buyer()
            + self._edifact_invoice_get_seller()
            + self._edifact_invoice_get_shipper()
            + header[11:]
        )
        return header

    def _edifact_invoice_get_product(self):
        number = 0
        segments = []
        vals = {}
        tax = {}
        for line in self.line_ids:
            if line.display_type != "product":
                continue
            order = line.sale_line_ids.order_id
            number += 1
            product_tax = 0
            product = line.product_id
            product_per_pack = line.product_uom_id._compute_quantity(
                line.quantity, product.uom_id
            )
            if line.tax_ids and line.tax_ids.amount_type == "percent":
                product_tax = line.tax_ids.amount
                if product_tax not in tax:
                    tax[product_tax] = line.price_total
                else:
                    tax[product_tax] += line.price_total
            product_seg = [
                # Line item number
                ("LIN", number, "", ["", "EN"]),
                # Product identification of supplier's article number
                ("PIA", "5", [product.id, "SA", "", "91"]),
                # Item description of product
                (
                    "IMD",
                    "ANM",
                    ["", "", "", product.product_tmpl_id.description_sale],
                ),
                # Invoiced quantity
                ("QTY", "47", line.quantity, line.product_uom_id.name),
                # Quantity per pack
                (
                    "QTY",
                    "52",
                    product_per_pack if product_per_pack else 1,
                    "PCE",
                ),  # TODO:check it again
                # Pieces delivered
                ("QTY", "46", line.sale_line_ids.qty_delivered),
                # Line item amount
                ("MOA", "203", line.price_total),
                # Calculation net
                ("PRI", ["AAA", round(line.price_total / line.quantity, 2)]),
                ("PRI", ["AAB", round(line.price_total / line.quantity, 2)]),
                # Order number of line item
                ("RFF", ["ON", order.id]),
                # Tax information
                (
                    "PRI",
                    "7",
                    "VAT",
                    "",
                    "",
                    ["", "", "", product_tax],
                ),  # TODO: check value this again later
                # Allowance or charge amount of line item
                ("MOA", ["8", "0"]),
            ]
            segments.extend(product_seg)
        vals["tax"] = tax
        vals["total_line_item"] = number
        return segments, vals

    def _edifact_invoice_get_summary(self, vals):
        tax_list = []
        total_line_item = vals["total_line_item"]
        if "tax" in vals:
            for product_tax, price_total in vals["tax"].items():
                # Tax Information
                tax_list.append(
                    ("TAX", "7", "VAT", "", price_total, ["", "", "", product_tax])
                )
                # Tax amount
                tax_list.append(("MOA", ["124", price_total * product_tax / 100]))
        summary = [
            ("UNS", "S"),
            # Number of line items in message
            ("CNT", ["2", total_line_item]),
            # Taxable amount
            ("MOA", ["125", self.amount_untaxed]),
            # Total amount
            ("MOA", ["128", self.amount_total]),
            # Tax amount
            ("MOA", ["124", self.amount_tax]),
            ("MOA", ["8", "0"]),
            ("UNT", 33 + 11 * total_line_item + 2 * len(vals["tax"]), "1"),
        ]
        summary = summary[:-2] + tax_list + summary[-2:]
        return summary
