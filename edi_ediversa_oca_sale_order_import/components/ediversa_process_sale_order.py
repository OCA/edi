# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import logging
from datetime import datetime

from odoo import _, api
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EdiversaProcessSaleOrder(Component):
    _name = "ediversa.process.sale.order"
    _usage = "input.process"
    _backend_type = "ediversa"
    _exchange_type = "ediversa_sale_input"
    _inherit = "edi.component.input.mixin"

    def process(self):
        exchange_record = self.exchange_record
        values = {"company_id": exchange_record.company_id.id}
        with io.BytesIO(base64.b64decode(exchange_record.exchange_file)) as f:
            lines = f.readlines()
            lines_group = []
            for line in lines:
                line = line.decode().rstrip("\n")
                elements = line.split("|")
                index = elements[0].lower()
                if lines_group and index in self._get_grouped_elems().get(
                    lines_group[0][0].lower()
                ):
                    lines_group.append(elements)
                elif lines_group:
                    if hasattr(self, f"{lines_group[0][0].lower()}_ediversa_values"):
                        getattr(self, f"{lines_group[0][0].lower()}_ediversa_values")(
                            values, lines_group
                        )
                    lines_group = []
                if index in self._get_grouped_elems():
                    lines_group.append(elements)
                elif hasattr(self, f"{index}_ediversa_values"):
                    getattr(self, f"{index}_ediversa_values")(values, elements)
        _logger.info(
            "Creating sale order from Ediversa with values "
            "{values} (Exchange record {exchange_record.name})"
        )
        sale_order = self.env["sale.order"].create(values)
        exchange_record.write({"model": "sale.order", "res_id": sale_order.id})
        _logger.info(f"Sale order created from Ediversa with ID {sale_order.id}")

    def _new_partner_vals(self, elements):
        elements_len = len(elements)
        if elements_len < 6:
            raise ValidationError(_("Missing new partner vals"))
        vals = {
            "ediversa_id": elements[1],
            "name": elements[5],
        }
        if elements_len >= 7:
            vals["street"] = elements[6]
        if elements_len >= 8:
            vals["city"] = elements[7]
        if elements_len >= 9:
            vals["zip"] = elements[8].rjust(5, "0") if elements[8] else ""
        return vals

    def _new_shipping_address_vals(self, elements):
        elements_len = len(elements)
        if elements_len < 2:
            raise ValidationError(_("Missing new shipping address vals"))
        vals = {"ediversa_id": elements[1], "type": "delivery"}
        if elements_len >= 4:
            vals["name"] = elements[3]
        if elements_len >= 5:
            vals["street"] = elements[4]
        if elements_len >= 6:
            vals["city"] = elements[5]
        if elements_len >= 7:
            vals["zip"] = elements[6].rjust(5, "0") if elements[6] else ""
        return vals

    def _new_invoice_address_vals(self, elements):
        elements_len = len(elements)
        if elements_len < 2:
            raise ValidationError(_("Missing new invoice address vals"))
        vals = {"ediversa_id": elements[1], "type": "invoice"}
        if elements_len >= 4:
            vals["name"] = elements[3]
        if elements_len >= 5:
            vals["street"] = elements[4]
        if elements_len >= 6:
            vals["city"] = elements[5]
        if elements_len >= 7:
            vals["zip"] = elements[6].rjust(5, "0") if elements[6] else ""
        return vals

    def create_customer(self, elements):
        return self.env["res.partner"].create(self._new_partner_vals(elements))

    def create_shipping_address(self, partner_id, elements):
        vals = self._new_shipping_address_vals(elements)
        vals["parent_id"] = partner_id
        return self.env["res.partner"].create(vals)

    def create_invoice_address(self, partner_id, elements):
        vals = self._new_invoice_address_vals(elements)
        vals["parent_id"] = partner_id
        return self.env["res.partner"].create(vals)

    @api.model
    def ord_ediversa_values(self, values, elements):
        """
        Name in Ediversa -> origin
        """
        values.update(
            {
                "origin": elements[1],
            }
        )

    @api.model
    def dtm_ediversa_values(self, values, elements):
        """
        Payment date in Ediversa -> date_order (it could be signed_on)
        Expected delivery date in Ediversa -> commitment_date
        """
        values.update(
            {
                "date_order": datetime.strptime(elements[1], "%Y%m%d").date()
                if elements[1]
                else False,
                "commitment_date": datetime.strptime(elements[2], "%Y%m%d").date()
                if elements[2]
                else False,
            }
        )

    @api.model
    def ftx_ediversa_values(self, values, elements):
        """
        Notes in Ediversa -> note
        """
        values.update(
            {
                "note": elements[3],
            }
        )

    @api.model
    def get_customer(self, elements):
        partner = self.env["res.partner"].search([("ediversa_id", "=", elements[1])])
        if len(partner) > 1:
            other_partner = partner.filtered(lambda a: a.type == "other")
            if other_partner:
                partner = other_partner[0]
            else:
                partner = partner[0]
        if not partner:
            partner = self.create_customer(elements)
        return partner

    @api.model
    def get_shipping_address(self, values, elements):
        partner = self.env["res.partner"].search([("ediversa_id", "=", elements[1])])
        if len(partner) > 1:
            shipping_partner = partner.filtered(lambda a: a.type == "delivery")
            if shipping_partner:
                partner = shipping_partner[0]
            else:
                partner = partner[0]
        if not partner:
            partner = self.create_shipping_address(values["partner_id"], elements)
        return partner

    @api.model
    def get_invoice_address(self, values, elements):
        partner = self.env["res.partner"].search([("ediversa_id", "=", elements[1])])
        if len(partner) > 1:
            invoice_partner = partner.filtered(lambda a: a.type == "invoice")
            if invoice_partner:
                partner = invoice_partner[0]
            else:
                invoice_partner = partner.filtered(
                    lambda a: a.parent_id.id == values["partner_id"]
                )
                if invoice_partner:
                    partner = invoice_partner[0]
            if len(partner) > 1:
                partner = partner[0]
        if not partner:
            partner = self.create_invoice_address(values["partner_id"], elements)
        return partner

    def nadby_ediversa_values(self, values, elements):
        """
        Customer -> partner_id
        """
        values.update({"partner_id": self.get_customer(elements).id})

    def naddp_ediversa_values(self, values, elements):
        """
        Shipping Address -> partner_shipping_id
        """
        values.update(
            {"partner_shipping_id": self.get_shipping_address(values, elements).id}
        )

    def nadiv_ediversa_values(self, values, elements):
        """
        Invoice Address -> partner_invoice_id
        """
        values.update(
            {"partner_invoice_id": self.get_invoice_address(values, elements).id}
        )

    def lin_imdlin_ediversa_values(self, values, elements):
        """
        Product description -> order_line.name
        """
        if elements[1] == "F":
            description = values.get("name") or ""
            description = f"{description}{elements[4]}"
            values["name"] = description

    def lin_qtylin_ediversa_values(self, values, elements):
        """
        Product quantity -> order_line.product_uom_qty
        """
        if elements[1] == "21":
            values["product_uom_qty"] = elements[2]

    def lin_prilin_ediversa_values(self, values, elements):
        """
        Unit price -> order_line.price_unit
        """
        if elements[1] == "AAB":
            values["price_unit"] = elements[2]

    def lin_ediversa_values(self, values, elements):
        """
        Invoice Address -> partner_invoice_id
        """
        line_vals = {}
        product = self.env["product.product"].search(
            [("barcode", "=", elements[0][1])], limit=1
        )
        if not product:
            raise ValidationError(
                _("Product with barcode %(barcode)s not found.", barcode=elements[0][1])
            )
        line_vals["product_id"] = product.id
        for element in elements[1:]:
            index = element[0].lower()
            if hasattr(self, f"lin_{index}_ediversa_values"):
                getattr(self, f"lin_{index}_ediversa_values")(line_vals, element)
        if values.get("order_line", False):
            values["order_line"].append((0, 0, line_vals))
        else:
            values["order_line"] = [(0, 0, line_vals)]

    def _get_grouped_elems(self):
        return {"lin": ["imdlin", "qtylin", "prilin"]}
