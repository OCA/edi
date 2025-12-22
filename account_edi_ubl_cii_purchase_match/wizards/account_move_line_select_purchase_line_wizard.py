# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLineSelectPurchaseLineWizard(models.TransientModel):

    _name = "account.move.line.select.purchase.line.wizard"
    _description = "account move line select purchase line wizard"
    partner_id = fields.Many2one(comodel_name="res.partner", readonly=True)
    description = fields.Char(related="move_line_id.name")
    move_line_id = fields.Many2one(
        comodel_name="account.move.line", readonly=True, required=True
    )
    currency_id = fields.Many2one(related="move_line_id.currency_id")

    move_line_quantity = fields.Float(related="move_line_id.quantity")
    move_line_price_unit = fields.Float(
        related="move_line_id.price_unit", string="Move line Unit Price"
    )
    move_line_price_subtotal = fields.Monetary(
        related="move_line_id.price_subtotal", string="Move line Subtotal"
    )

    product_id = fields.Many2one(
        comodel_name="product.product", domain="product_domain"
    )
    product_domain = fields.Binary(compute="_compute_product_domain")
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('purchase', 'done'))]",
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Line",
        domain="[('order_id', '=', purchase_order_id), ('product_id', '=', product_id)]",
        compute="_compute_purchase_order_line_id",
        store=True,
        readonly=False,
    )
    po_line_product_uom_qty = fields.Float(
        related="purchase_order_line_id.product_uom_qty", string="Ordered Qty"
    )
    po_line_qty_received = fields.Float(related="purchase_order_line_id.qty_received")
    po_line_qty_invoiced = fields.Float(related="purchase_order_line_id.qty_invoiced")
    po_line_price_unit = fields.Float(
        related="purchase_order_line_id.price_unit", string="PO line Unit Price"
    )
    po_line_price_subtotal = fields.Monetary(
        related="purchase_order_line_id.price_subtotal", string="PO line Subtotal"
    )

    @api.depends("purchase_order_id")
    def _compute_product_domain(self):
        for rec in self:
            rec.product_domain = [
                ("id", "in", rec.purchase_order_id.order_line.product_id.ids)
            ]

    def select_purchase_line(self):
        for rec in self:
            if rec.move_line_id.purchase_line_id:
                continue
            rec.move_line_id._set_product(rec.purchase_order_line_id.product_id)
            rec.move_line_id.purchase_line_id = rec.purchase_order_line_id
            rec.move_line_id._update_product_supplier_name()

    @api.depends("product_id", "purchase_order_id")
    def _compute_purchase_order_line_id(self):
        for rec in self:
            line = rec.purchase_order_id.order_line.filtered(
                lambda pl: pl.product_id == rec.product_id
            )
            if len(line) == 1:
                rec.purchase_order_line_id = line
            else:
                rec.purchase_order_line_id = False
