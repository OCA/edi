# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import api, fields, models


class ReportVoxelPicking(models.AbstractModel):
    _name = 'report.edi_voxel_stock_picking.template_voxel_picking'

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids[:1])
        return {
            'general': self._get_general_data(docs),
            'supplier': self._get_suplier_data(docs),
            'client': self._get_client_data(docs),
            'customers': self._get_customers_data(docs),
            'comments': self._get_comments_data(docs),
            'references': self._get_references_data(docs),
            'products': self._get_products_data(docs),
        }

    # report data. Auxiliary methods
    # ------------------------------
    def _get_general_data(self, picking):
        type_mapping = {'outgoing': 'AlbaranComercial',
                        'incoming': 'AlbaranAbono'}
        date = fields.Datetime.from_string(picking.date)
        return {
            'Type': type_mapping.get(picking.picking_type_code),
            'Ref': picking.name,
            'Date': date and datetime.strftime(date, "%Y-%m-%d")
        }

    def _get_suplier_data(self, picking):
        supplier = picking.company_id.partner_id
        return {
            'CIF': supplier.vat,
            'Company': supplier.name,
            'Address': ', '.join(
                filter(None, [supplier.street, supplier.street2])),
            'City': supplier.city,
            'PC': supplier.zip,
            'Province': supplier.state_id.name,
            'Country': supplier.country_id.code,
            'Email': supplier.email,
        }

    def _get_client_data(self, picking):
        client = picking.sale_id.partner_invoice_id or picking.partner_id
        return {
            'SupplierClientID': client.ref,
            'CIF': client.vat,
            'Company': client.commercial_partner_id.name,
            'Address': ', '.join(
                filter(None, [client.street, client.street2])),
            'City': client.city,
            'PC': client.zip,
            'Province': client.state_id.name,
            'Country': client.country_id.code_alpha3,
            'Email': client.email,
        }

    def _get_customers_data(self, picking):
        customer = picking.partner_id
        client = picking.sale_id.partner_invoice_id or picking.partner_id
        return [{
            'SupplierClientID': client.ref,
            'SupplierCustomerID': customer.ref,
            'Customer': customer.name,
            'Address': ', '.join(
                filter(None, [customer.street, customer.street2])),
            'City': customer.city,
            'PC': customer.zip,
            'Province': customer.state_id.name,
            'Country': customer.country_id.code,
            'Email': customer.email,
        }]

    def _get_comments_data(self, picking):
        return picking.note and [{'Msg': picking.note}] or []

    def _get_references_data(self, picking):
        so = picking.sale_id
        return [{
            'PORef': (
                so.client_order_ref or so.name
            ) if so else picking.origin,
        }]

    def _get_products_data(self, picking):
        return [{
            'product': self._get_product_data(line),
        } for line in picking.move_lines]

    def _get_product_data(self, line):
        return {
            'SupplierSKU': line.product_id.default_code,
            'Item': line.product_id.name,
            'Qty': str(line.product_uom_qty),
            'MU': line.product_uom.voxel_code,
        }
