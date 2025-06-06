# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _ediversa_invoice_get_header(self):
        self.ensure_one()
        inv_type = ""
        if self.move_type == "out_invoice":
            inv_type = "380"
        elif self.move_type == "out_refund":
            inv_type = "381"

        sale = self.env["sale.order"]
        # Only 1 sale order is considered
        if self.invoice_line_ids.sale_line_ids:
            sale = self.invoice_line_ids.sale_line_ids[0].order_id
        # Only 1 picking is considered
        picking = self.env["stock.picking"]
        pickings = sale.picking_ids.filtered(
            lambda picking: picking.state not in ["draft", "cancel"]
            and picking.picking_type_code == "outgoing"
        )
        if pickings:
            picking = pickings[0]
        commercial_partner = self.partner_id.commercial_partner_id
        company = self.company_id
        company_vat = company.vat or ""
        shipping_address = self.partner_shipping_id
        if company_vat.startswith(company.country_id.code):
            company_vat = company_vat.replace(company.country_id.code, "")
        header = [
            ("INVOIC_D_93A_UN_EAN007",),
            # Invoice info
            ("INV", self.name and self.name[:17] or "", inv_type, "9"),
            # Invoice date
            ("DTM", self.invoice_date.strftime("%Y%m%d")),
            # Customer
            (
                "NADBY",
                self.partner_id.ediversa_id or "",
                self.partner_id.name and self.partner_id.name[:70] or "",
                f"{self.partner_id.street or ''} {self.partner_id.street2 or ''}"[:70],
                self.partner_id.city and self.partner_id.city[:35] or "",
                self.partner_id.zip and self.partner_id.zip[:5] or "",
                self.partner_id.vat and self.partner_id.vat[:11] or "",
                # Section/Departmen of customer who made the purchase
                "",
                self.partner_id.country_id.code or "",
            ),
            # Invoice partner (in examples, they use the same as customer)
            (
                "NADIV",
                self.partner_id.ediversa_id or "",
                self.partner_id.name and self.partner_id.name[:70] or "",
                f"{self.partner_id.street or ''} {self.partner_id.street2 or ''}"[:70],
                self.partner_id.city and self.partner_id.city[:35] or "",
                self.partner_id.zip and self.partner_id.zip[:5] or "",
                self.partner_id.vat and self.partner_id.vat[:11] or "",
            ),
            # Legal customer
            (
                "NADBCO",
                commercial_partner.ediversa_id or "",
                commercial_partner.name and commercial_partner.name[:70] or "",
                f"{commercial_partner.street or ''} {commercial_partner.street2 or ''}"[
                    :70
                ],
                commercial_partner.city and commercial_partner.city[:35] or "",
                commercial_partner.zip and commercial_partner.zip[:5] or "",
                commercial_partner.vat and commercial_partner.vat[:11] or "",
                commercial_partner.country_id.code
                and commercial_partner.country_id.code[:2]
                or "",
            ),
            # Provider
            (
                "NADSU",
                company.partner_id.ediversa_id or "",
                company.name and company.name[:70] or "",
                # Commercial Registry
                "",
                f"{company.street or ''} {company.street2 or ''}"[:35],
                company.city and company.city[:35] or "",
                company.zip and company.zip[:5] or "",
                company_vat and company_vat[:11] or "",
            ),
            # Legal provider
            (
                "NADSCO",
                company.partner_id.ediversa_id or "",
                company.name and company.name[:70] or "",
                # Commercial Registry
                "",
                f"{company.street or ''} {company.street2 or ''}"[:70],
                company.city and company.city[:35] or "",
                company.zip and company.zip[:5] or "",
                company_vat and company_vat[:11] or "",
            ),
            # Receiver
            (
                "NADDP",
                self.partner_shipping_id.ediversa_id or "",
                self.partner_shipping_id.name
                and self.partner_shipping_id.name[:70]
                or "",
                f"{shipping_address.street or ''} {shipping_address.street2 or ''}"[
                    :70
                ],
                self.partner_shipping_id.city
                and self.partner_shipping_id.city[:35]
                or "",
                self.partner_shipping_id.zip and self.partner_shipping_id.zip[:5] or "",
            ),
            # EDI code of the "parter"
            ("NADPR", commercial_partner.ediversa_id or ""),
            # Currency
            (
                "CUX",
                self.currency_id.name and self.currency_id.name[:3] or "",
                # 4 value means invoice currency
                "4",
            ),
        ]
        if sale:
            header.append(
                (
                    "RFF",
                    "ON",
                    sale.name and sale.name.replace("|", "_")[:17] or "",
                    sale.date_order.strftime("%Y%m%d"),
                )
            )
        if picking:
            header.append(
                (
                    "RFF",
                    "DQ",
                    picking.name and picking.name.replace("|", "_")[:17] or "",
                    picking.scheduled_date.strftime("%Y%m%d"),
                )
            )
        return header

    def _ediversa_invoice_get_line(self):
        self.ensure_one()
        lines = []
        count = 1
        for line in self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        ):
            values = line._ediversa_invoice_line_vals(count)
            lines += values
            count += 1
        return lines

    def _ediversa_invoice_get_summary(self):
        total_no_discount = sum(
            line.quantity * line.price_unit for line in self.invoice_line_ids
        )
        return [
            ("CNTRES", "2"),
            (
                "MOARES",
                str(self.amount_untaxed),
                str(total_no_discount),
                str(self.amount_untaxed),
                str(self.amount_total),
                str(self.amount_tax),
            ),
        ] + self._ediversa_get_taxes()

    def _ediversa_get_taxes(self):
        taxes = []
        for tax in self.line_ids.filtered(lambda line: line.tax_ids).mapped("tax_ids"):
            lines = self.invoice_line_ids.filtered(
                lambda line, tax=tax: tax.id in line.tax_ids.ids
            )
            base = sum(lines.mapped("price_subtotal"))
            amount = tax._compute_amount(base, base)
            taxes.append(
                (
                    "TAXRES",
                    tax.ediversa_tax_type,
                    str(tax.amount),
                    str(amount),
                    str(base),
                )
            )
        return taxes
