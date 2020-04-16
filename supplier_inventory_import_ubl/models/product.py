# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = "product.product"

    supplier_stock = fields.Float(
        string="Supplier Stock",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Information updated by the last supplier inventory report (UBL Edi)",
    )
    supplier_stock_info = fields.Char(
        string="Supplier Stock Info",
        readonly=True,
        help="Contextual info on last supplier stock updated with UBL import",
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
        """ Mainly used in stock quant screen and for reports
            You may customize it
        """
        return "%s on %s" % (supplier.name[:5], update_date)
