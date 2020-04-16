# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    stock = fields.Float(
        string="Stock Qty",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Vendor stock quantity available",
    )
    last_stock = fields.Date(
        string="Last Stock", help="Date of the last known supplier stock",
    )
    product_default_code = fields.Char(
        string="Internal reference", store=False,
        compute="_compute_product_default_code", help="Default code of product")

    @api.multi
    def _update_supplier_stock_from_ubl_inventory(
        self, supplier, stock_by_tmpl, inventory_date
    ):
        for rec in self:
            if rec.product_tmpl_id and stock_by_tmpl.get(rec.product_tmpl_id.id):
                rec.write(
                    {"stock": stock_by_tmpl[rec.product_tmpl_id.id],
                     "last_stock": inventory_date, }
                )

    @api.multi
    def _compute_product_default_code(self):
        """ Display default_code only when there is only 1 variant by template
        """
        template_ids = self.mapped("product_tmpl_id").ids
        products = self.env["product.product"].search(
            [("product_tmpl_id", "in", template_ids)], order="product_tmpl_id")
        templates = defaultdict(list)
        for prd in products:
            templates[prd.product_tmpl_id].append(prd.default_code)
        for rec in self:
            if len(templates[rec.product_tmpl_id]) == 1:
                rec.product_default_code = templates[rec.product_tmpl_id][0]
            else:
                rec.product_default_code = False
