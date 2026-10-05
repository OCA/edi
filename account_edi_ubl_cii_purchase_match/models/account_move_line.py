# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal

from odoo import Command, _, api, fields, models
from odoo.tools import float_compare, format_amount, formatLang


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"
    supplier_product_code = fields.Char(readonly=True)
    purchase_line_mismatch = fields.Boolean(
        compute="_compute_purchase_line_mismatch",
        help="Checked when this invoice line does not fully match its related purchase"
        " order line.",
    )
    purchase_line_mismatch_summary = fields.Char(
        compute="_compute_purchase_line_mismatch",
        help="Short description of the purchase order matching issue.",
    )
    purchase_line_quantity_mismatch = fields.Boolean(
        compute="_compute_purchase_line_mismatch",
        help=(
            "Checked when this invoice line has a quantity mismatch with its related "
            "purchase order line."
        ),
    )
    purchase_line_quantity_mismatch_details = fields.Text(
        compute="_compute_purchase_line_mismatch",
        help=(
            "Human-readable description of the quantity differences between this "
            "invoice line and the related purchase order line."
        ),
    )
    purchase_line_other_mismatch = fields.Boolean(
        compute="_compute_purchase_line_mismatch",
        help=(
            "Checked when this invoice line has a non-quantity mismatch with its "
            "related purchase order line."
        ),
    )
    purchase_line_other_mismatch_details = fields.Text(
        compute="_compute_purchase_line_mismatch",
        help=(
            "Human-readable description of the non-quantity differences between this "
            "invoice line and the related purchase order line."
        ),
    )

    def _update_product_supplier_name(self):
        for rec in self:
            if not rec.name or not rec.product_id:
                continue
            partner = rec.move_id.partner_id
            product = rec.product_id
            product_tmpl = rec.product_id.product_tmpl_id

            def is_matching_seller(
                seller, partner=partner, product=product, product_tmpl=product_tmpl
            ):
                return seller.partner_id == partner and (
                    seller.product_id == product
                    or seller.product_tmpl_id == product_tmpl
                )

            seller = rec.product_id.seller_ids.filtered(is_matching_seller)
            if not seller:
                rec.product_id.seller_ids.create(
                    {
                        "product_id": rec.product_id.id,
                        "product_code": rec.supplier_product_code,
                        "price": rec.price_unit,
                    }
                )
            else:
                if rec.supplier_product_code:
                    seller.product_code = rec.supplier_product_code

    def action_select_purchase_line(self):
        self.ensure_one()
        purchase_orders = self.purchase_line_id.order_id
        partner = self.move_id.partner_id
        if not purchase_orders and self.move_id.invoice_origin:
            po_candidates = self.move_id._extract_purchase_references_from_origin()
            purchase_orders = self.env["purchase.order"].search(
                [
                    ("name", "in", po_candidates),
                    ("state", "in", ("purchase", "done")),
                    ("partner_id", "=", partner.id),
                ]
            )
        context = {
            **self.env.context,
            **{
                "default_move_line_id": self.id,
                "default_partner_id": partner.id,
                "default_purchase_order_ids": [Command.set(purchase_orders.ids)],
                "default_purchase_order_line_id": self.purchase_line_id.id,
            },
        }
        return {
            "type": "ir.actions.act_window",
            "name": "Select Purchase Line",
            "res_model": "account.move.line.select.purchase.line.wizard",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def action_show_purchase_line(self):
        self.ensure_one()
        if not self.purchase_line_id:
            return {}
        form = self.env.ref(
            "account_edi_ubl_cii_purchase_match.purchase_order_line_form_view"
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.purchase_line_id.display_name,
            "res_model": self.purchase_line_id._name,
            "view_mode": "form",
            "views": [(form.id, "form")],
            "view_id": form.id,
            "res_id": self.purchase_line_id.id,
            "target": "new",
            "context": self.env.context,
        }

    def _set_product(self, product):
        self.ensure_one()
        price_unit = self.price_unit
        self.product_id = product
        self.price_unit = price_unit

    # Purchase line mismatch logic

    @api.depends(
        "purchase_line_id",
        "move_id.state",
        "price_unit",
        "price_subtotal",
        "quantity",
    )
    def _compute_purchase_line_mismatch(self):
        for rec in self:
            if not rec.purchase_line_id or rec.move_id.state != "draft":
                rec._reset_purchase_line_mismatch()
                continue

            rec._set_purchase_line_mismatch(
                *rec._get_purchase_line_mismatch_differences()
            )

    def _reset_purchase_line_mismatch(self):
        self.purchase_line_mismatch = False
        self.purchase_line_mismatch_summary = False
        self.purchase_line_quantity_mismatch = False
        self.purchase_line_quantity_mismatch_details = False
        self.purchase_line_other_mismatch = False
        self.purchase_line_other_mismatch_details = False

    def _get_purchase_line_mismatch_differences(self):
        self.ensure_one()
        quantity_differences = []
        other_differences = []
        po_line = self.purchase_line_id
        precision = self.currency_id.rounding or 0.01
        if (
            float_compare(
                self.price_unit,
                po_line.price_unit,
                precision_rounding=precision,
            )
            != 0
        ):
            other_differences.append(
                _(
                    "Invoice unit price is %(invoice_price)s; purchase order unit "
                    "price is %(po_price)s.",
                    invoice_price=format_amount(
                        self.env, self.price_unit, self.currency_id
                    ),
                    po_price=format_amount(
                        self.env, po_line.price_unit, po_line.currency_id
                    ),
                )
            )
        if (
            float_compare(
                po_line.qty_invoiced,
                po_line.product_uom_qty,
                precision_rounding=po_line.product_uom.rounding or 0.01,
            )
            > 0
        ):
            quantity_differences.append(
                _(
                    "Total invoiced quantity is %(invoiced_qty)s; ordered quantity is "
                    "%(ordered_qty)s.",
                    invoiced_qty=self._format_purchase_quantity(
                        po_line.qty_invoiced, po_line.product_uom
                    ),
                    ordered_qty=self._format_purchase_quantity(
                        po_line.product_uom_qty, po_line.product_uom
                    ),
                )
            )
        if (
            po_line.product_id.purchase_method == "receive"
            and float_compare(
                po_line.qty_received,
                po_line.qty_invoiced,
                precision_rounding=po_line.product_uom.rounding or 0.01,
            )
            < 0
        ):
            quantity_differences.append(
                _(
                    "Total invoiced quantity is %(invoiced_qty)s; received quantity "
                    "is %(received_qty)s.",
                    invoiced_qty=self._format_purchase_quantity(
                        po_line.qty_invoiced, po_line.product_uom
                    ),
                    received_qty=self._format_purchase_quantity(
                        po_line.qty_received, po_line.product_uom
                    ),
                )
            )
        return quantity_differences, other_differences

    def _format_purchase_quantity(self, quantity, uom):
        rounding = Decimal(str(uom.rounding or 0.01)).normalize()
        digits = max(0, -rounding.as_tuple().exponent)
        return formatLang(self.env, quantity, digits=digits)

    def _get_purchase_mismatch_product_label(self):
        self.ensure_one()
        return self.product_id.display_name or self.name or _("No product")

    def _set_purchase_line_mismatch(self, quantity_differences, other_differences):
        differences = quantity_differences + other_differences
        self.purchase_line_mismatch = bool(differences)
        self.purchase_line_quantity_mismatch = bool(quantity_differences)
        self.purchase_line_quantity_mismatch_details = (
            "\n".join(quantity_differences) if quantity_differences else False
        )
        self.purchase_line_other_mismatch = bool(other_differences)
        self.purchase_line_other_mismatch_details = (
            "\n".join(other_differences) if other_differences else False
        )
        if quantity_differences and other_differences:
            self.purchase_line_mismatch_summary = _("Quantity and price mismatch")
        elif quantity_differences:
            self.purchase_line_mismatch_summary = _("Quantity mismatch")
        elif other_differences:
            self.purchase_line_mismatch_summary = _("Price mismatch")
        else:
            self.purchase_line_mismatch_summary = False

    def action_show_purchase_line_mismatch_details(self):
        self.ensure_one()
        product_label = self._get_purchase_mismatch_product_label()
        quantity_messages = (
            self.purchase_line_quantity_mismatch_details or ""
        ).splitlines()
        other_messages = (self.purchase_line_other_mismatch_details or "").splitlines()
        for message in quantity_messages:
            self.env.user.notify_danger(
                message=_(
                    "%(product)s: %(message)s",
                    product=product_label,
                    message=message,
                ),
                title=_("Quantity mismatch"),
                sticky=True,
            )
        for message in other_messages:
            self.env.user.notify_warning(
                message=_(
                    "%(product)s: %(message)s",
                    product=product_label,
                    message=message,
                ),
                title=_("Price mismatch"),
                sticky=True,
            )
        if not (
            self.purchase_line_quantity_mismatch_details
            or self.purchase_line_other_mismatch_details
        ):
            self.env.user.notify_warning(
                message=_(
                    "%(product)s: %(message)s",
                    product=product_label,
                    message=self.purchase_line_mismatch_summary,
                ),
                title=_("Purchase mismatch details"),
                sticky=True,
            )
        return True
