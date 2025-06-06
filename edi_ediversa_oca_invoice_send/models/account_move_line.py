# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _ediversa_invoice_get_taxes(self):
        self.ensure_one()
        taxes = tuple()
        for tax in self.tax_ids:
            taxes += (
                "TAXLIN",
                tax.ediversa_tax_type,
                str(tax.amount),
                str((tax.amount / 100) * self.price_subtotal),
            )
        return taxes

    def _ediversa_invoice_line_vals(self, count):
        self.ensure_one()
        # PCE means units, value by default
        uom = "PCE"
        if self.product_uom_id.id == self.env.ref("uom.product_uom_kgm").id:
            uom = "KGM"
        elif self.product_uom_id.id == self.env.ref("uom.product_uom_litre").id:
            uom = "LTR"
        elif self.product_uom_id.id == self.env.ref("uom.product_uom_cubic_meter").id:
            uom = "MTQ"
        elif self.product_uom_id.id == self.env.ref("uom.product_uom_ton").id:
            uom = "TNE"
        elif self.product_uom_id.id == self.env.ref("uom.product_uom_meter").id:
            uom = "MTR"

        net_price = self.price_subtotal / self.quantity if self.quantity else 0.0

        return [
            ("LIN", self.product_id.barcode, "EN", str(count)),
            # Product description
            (
                "IMDLIN",
                self.name[:70] if self.name else "",
                "S" if self.product_id.type == "service" else "M",
                # F means description with free text
                "F",
            ),
            (
                "QTYLIN",
                "61" if self.move_id.move_type == "out_refund" else "47",
                str(self.quantity),
                uom,
            ),
            # Net price
            ("PRILIN", "AAA", str(net_price)),
            # Gross price
            ("PRILIN", "AAB", str(self.price_unit)),
            self._ediversa_invoice_get_taxes(),
            ("MOALIN", str(self.price_subtotal)),
        ]
