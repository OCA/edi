# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from openerp.addons import decimal_precision as dp


HELP_STK = _("Contextual info on last supplier stock updated with UBL import")
HELP_INF = _("Information updated by the last supplier inventory report (UBL Edi)")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    supplier_stock = fields.Float(
        string="Supplier Stock",
        readonly=True,
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
        compute="_compute_supplier_stock_fields",
        help=HELP_STK,
    )
    supplier_stock_info = fields.Char(
        string="Supplier Stock Info",
        readonly=True,
        store=True,
        compute="_compute_supplier_stock_fields",
        help=HELP_INF + "\nIf ⚠ is displayed, check supplier stock on variants to get "
        "specific stock information on a particular product",
    )

    @api.multi
    @api.depends("product_variant_ids.supplier_stock")
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
    _inherit = "product.product"

    supplier_stock = fields.Float(
        string="Supplier Stock",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
        help=HELP_STK,
    )
    supplier_stock_info = fields.Char(
        string="Supplier Stock Info",
        readonly=True,
        help=HELP_INF,
    )

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
        """Mainly used in stock quant screen and for reports
        You may customize it
        """
        return "%s on %s" % (supplier.name[:5], update_date)
