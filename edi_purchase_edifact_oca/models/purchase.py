# Copyright 2024 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import _, models, fields
from datetime import datetime
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    edifact_version = fields.Selection(
        [
            ("d96a", "D.96A"),
            ("d01b", "D.01B"),
        ],
        default="d96a",
        string="Edifact Version",
    )

    def _replace_edifact_delimiters(self, data):
        edifact_delimiters = {"+", ":", ".", "?", "*"}

        def replace_in_string(s):
            return "".join(
                char if char not in edifact_delimiters else "_" for char in s
            )

        def process_element(element):
            if isinstance(element, str):
                return (
                    replace_in_string(element)
                    if not element.replace(".", "", 1).isdigit()
                    else element
                )
            elif isinstance(element, (list, tuple)):
                result = map(process_element, element)
                return type(element)(result)
            else:
                return element

        return process_element(data)

    def edifact_purchase_generate_data(self, exchange_record=None):
        self.ensure_one()
        edifact_model = self.env["base.edifact"]
        lines = []
        interchange = self._edifact_purchase_get_interchange()

        header = self._edifact_purchase_get_header(exchange_record)
        product, vals = self._edifact_purchase_get_product()
        summary = self._edifact_purchase_get_summary(vals, exchange_record)
        lines += header + product + summary
        for segment in lines:
            segment = self._replace_edifact_delimiters(segment)
            interchange.add_segment(edifact_model.create_segment(*segment))
        return f"UNA:+.? '{interchange.serialize()}"

    def _edifact_purchase_get_interchange(self):
        id_number = self.env["res.partner.id_number"]
        # Because the person placing the order will be
        # the representative of the ordering company.
        # So we will check the code of the company's `id number` here
        sender = id_number.search(
            [("partner_id", "=", self.user_id.company_id.partner_id.id)], limit=1
        )
        recipient = id_number.search([("partner_id", "=", self.partner_id.id)], limit=1)
        # if current supplier does not have `Id number`
        # then check current supplier's parent
        if not recipient and self.partner_id.parent_id:
            recipient = id_number.search(
                [("partner_id", "=", self.partner_id.parent_id.id)], limit=1
            )
        if not sender or not recipient:
            raise UserError(_("Partner is not allowed to use the feature."))
        sender_edifact = [sender.name, "14"]
        recipient_edifact = [recipient.name, "14"]
        syntax_identifier = ["UNOC", "3"]

        return self.env["base.edifact"].create_interchange(
            sender_edifact, recipient_edifact, self.name, syntax_identifier
        )

    def _edifact_purchase_get_address(self, partner):
        # We apply the same logic as:
        # https://github.com/OCA/edi/blob/
        # c41829a8d986c6751c07299807c808d15adbf4db/base_ubl/models/ubl.py#L39

        # oca/partner-contact/partner_address_street3 is installed
        if hasattr(partner, "street3"):
            return partner.street3 or partner.street2 or partner.street
        else:
            return partner.street2 or partner.street

    def _edifact_get_name_and_address(self, partner, code, id_number=""):
        street = self._edifact_purchase_get_address(partner)
        return [
            # partner information
            (
                "NAD",
                code,
                [id_number, "", "9"],
                "",
                partner.commercial_company_name,
                [street, ""],
                partner.city,
                partner.state_id.name,
                partner.zip,
                partner.country_id.code,
            ),
            # VAT registration number
            ("RFF", ["VA", partner.vat]),
            # Purchasing contact
            ("CTA", "PD", [partner.name, ""]),
        ]

    def _edifact_purchase_get_header(self, exchange_record=None):
        today = datetime.now().date().strftime("%Y%m%d")
        id_number = self.env["res.partner.id_number"]
        buyer_id_number = id_number.search(
            [("partner_id", "=", self.user_id.company_id.partner_id.id)], limit=1
        )
        seller_id_number = id_number.search([("partner_id", "=", self.partner_id.id)])
        if not seller_id_number and self.partner_id.parent_id:
            seller_id_number = id_number.search(
                [("partner_id", "=", self.partner_id.parent_id.id)], limit=1
            )
        message_id = exchange_record.id if exchange_record else ""
        warehouse_name = (
            self.picking_type_id.warehouse_id.name if self.picking_type_id else ""
        )

        header = [
            ("UNH", message_id, ["ORDERS", "D", "96A", "UN", "EAN008"]),
            # Order
            ("BGM", ["220", "", "9", "ORDERS"], self.name, "9"),
            # 137: Document/message date/time
            ("DTM", ["137", today, "102"]),
            # 2: Delivery date/time, requested
            ("DTM", ["2", self.date_planned.strftime("%Y%m%d"), "102"]),
            # Delivery note number
            ("RFF", ["DQ", self.id]),
            # Telephone
            ("COM", [self.user_id.partner_id.phone or "", "TE"]),
            # Reference currency
            ("CUX", ["2", self.currency_id.name, "4"]),
            # Rate of exchange
            ("DTM", ["134", today, "102"]),
            # Main-carriage transport
            ("TDT", "20", "", "30", "31"),  # TODO: add detail of transport
            # Warehouse
            (
                "LOC",
                "18",
                [warehouse_name, "", "", "", ""],
            ),
        ]
        if self.edifact_version == "d01b":
            header[0] = (
                "UNH",
                message_id,
                ["ORDERS", "D", "01B", "UN", "EAN010"],
            )

        if not self.user_id.partner_id.phone:
            header = header[:5] + header[6:]

        header = (
            header[:5]
            + self._edifact_get_name_and_address(
                self.user_id.partner_id, "BY", buyer_id_number.name
            )
            + self._edifact_get_name_and_address(
                self.partner_id, "SU", seller_id_number.name
            )
            + self._edifact_get_name_and_address(
                self.picking_type_id.warehouse_id.partner_id, "DP", buyer_id_number.name
            )
            + header[5:]
        )

        return header

    def _edifact_purchase_get_product(self):
        number = 0
        segments = []
        vals = {}
        tax = {}
        for line in self.order_line:
            number += 1
            product_tax = 0
            product = line.product_id
            if line.taxes_id and line.taxes_id.amount_type == "percent":
                product_tax = line.taxes_id.amount
                if product_tax not in tax:
                    tax[product_tax] = line.price_total
                else:
                    tax[product_tax] += line.price_total
            product_type = "EN"
            if self.edifact_version == "d01b":
                product_type = "SRV"
            product_seg = [
                # Line item number
                ("LIN", number, "", [product.barcode, product_type]),
                # Product identification of Supplier's article number
                ("PIA", "1", [product.default_code, "SA", "", "91"]),
                # Product identification of Buyer's part number
                ("PIA", "1", [product.default_code, "BP", "", "92"]),
                # Ordered quantity
                ("QTY", ["21", line.product_uom_qty, ""]),
                # Quantity per pack
                (
                    "QTY",
                    [
                        "52",
                        line.package_qty if "package_qty" in line._fields else "",
                        "",
                    ],
                ),
                # Delivery date/time, requested
                ("DTM", ["2", line.date_planned.strftime("%Y%m%d"), "102"]),
                # Line item amount
                ("MOA", ["203", line.price_total]),
                # Mutually defined
                # ("FTX", "ZZZ", "1", ["", "", "91"]),
                # Calculation net
                ("PRI", ["AAA", round(line.price_total / line.product_uom_qty, 2)]),
                ("PRI", ["AAB", round(line.price_total / line.product_uom_qty, 2)]),
                # Order number of line item
                ("RFF", ["PL", self.id]),
                # TODO: This place can add delivery to multiple locations
                # Tax information
                ("TAX", "7", "VAT", "", "", ["", "", "", product_tax]),
            ]
            segments.extend(product_seg)
        # Pass tax information to summary
        # TODO: can be used to create TAX, MOA segments
        vals["tax"] = tax
        vals["total_line_item"] = number
        return segments, vals

    def _edifact_purchase_get_summary(self, vals, exchange_record=None):
        message_id = exchange_record.id if exchange_record else ""
        total_line_item = vals["total_line_item"]
        len_header = 22
        if not self.user_id.partner_id.phone:
            len_header -= 1
        summary = [
            ("UNS", "S"),
            # Number of line items in message
            ("CNT", ["2", total_line_item]),
            ("UNT", len_header + 9 * total_line_item, message_id),
        ]
        return summary
