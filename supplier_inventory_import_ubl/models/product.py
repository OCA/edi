# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


HELP = "Contextual info on last supplier stock updated with UBL import"


class ProductSupplierInventoryUblMixin(models.AbstractModel):
    _name = "product.supplier.inventory.ubl.mixin"

    supplier_stock = fields.Float(
        string="Supplier Stock",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
        help="Information updated by the last supplier inventory report (UBL Edi)",
    )
    supplier_stock_info = fields.Char(
        string="Supplier Stock Info", readonly=True, help=HELP,
    )


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "product.supplier.inventory.ubl.mixin"]

    supplier_stock = fields.Float(compute="_compute_supplier_stock_fields")
    supplier_stock_info = fields.Char(
        compute="_compute_supplier_stock_fields",
        help=HELP + "\nIf ⚠ is displayed, check supplier stock on variants to get "
        "specific stock information on a particular product",
    )

    @api.multi
    def _compute_supplier_stock_fields(self):
        for rec in self:
            stock_info = set([x.supplier_stock_info for x in rec.product_variant_ids])
            if len(stock_info) == 1:
                rec.supplier_stock_info = stock_info.pop()
                rec.supplier_stock = sum(
                    [x.supplier_stock for x in rec.product_variant_ids]
                )
            else:
                # It's a non sense to sum stock value if supplier or date
                # are different, then we define an alert explained in help
                rec.supplier_stock_info = "⚠"
                rec.supplier_stock = 0


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "product.supplier.inventory.ubl.mixin"]

    @api.multi
    def _update_supplier_stock_from_ubl_inventory(
        self, supplier, stock_by_product, update_date
    ):
        info = self._set_stock_info_from_ubl_inventory(supplier, update_date)
        for rec in self:
            rec.write(
                {
                    "supplier_stock": stock_by_product[rec.id],
                    "supplier_stock_info": info,
                }
            )

    @api.model
    def _set_stock_info_from_ubl_inventory(self, supplier, update_date):
        """ Mainly used in stock quant screen and for reports
            You may customize it
        """
        return "%s on %s" % (supplier.name[:5], update_date)
