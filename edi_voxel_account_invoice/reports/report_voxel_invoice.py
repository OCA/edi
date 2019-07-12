# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime
from operator import itemgetter
from odoo import api, fields, models


class ReportVoxelInvoice(models.AbstractModel):
    _name = 'report.edi_voxel_account_invoice.template_voxel_invoice'

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['account.invoice'].browse(docids)[:1]
        data = {
            'general': self._get_general_data(docs),
            'supplier': self._get_suplier_data(docs),
            'client': self._get_client_data(docs),
            'customers': self._get_customers_data(docs),
            'comments': self._get_comments_data(docs),
            'references': self._get_references_data(docs),
            'products': self._get_products_data(docs),
            'taxes': self._get_taxes_data(docs),
            'tota_summary': self._get_total_summary_data(docs),
        }
        return data

    # report data. Auxiliary methods
    def _get_general_data(self, invoice):
        type_mapping = {'out_invoice': 'FacturaComercial',
                        'out_refund': 'FacturaAbono'}
        date_invoice = fields.Datetime.from_string(invoice.date_invoice)
        return {
            'Type': type_mapping.get(invoice.type),
            'Ref': invoice.number,
            'Date': date_invoice and datetime.strftime(
                date_invoice, "%Y-%m-%d"),
            'Currency': invoice.currency_id.name,
        }

    def _get_suplier_data(self, invoice):
        supplier = invoice.company_id.partner_id
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

    def _get_client_data(self, invoice):
        client = invoice.partner_id
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

    def _get_customers_data(self, invoice):
        return [{
            'SupplierClientID': invoice.partner_id.ref,
            'SupplierCustomerID': customer.ref,
            'Customer': customer.name,
            'Address': ', '.join(
                filter(None, [customer.street, customer.street2])),
            'City': customer.city,
            'PC': customer.zip,
            'Province': customer.state_id.name,
            'Country': customer.country_id.code,
            'Email': customer.email,
        } for customer in invoice.mapped('picking_ids.partner_id')]

    def _get_comments_data(self, invoice):
        return invoice.comment and [{'Msg': invoice.comment}] or []

    def _get_references_data(self, invoice):
        references = []
        if invoice.picking_ids:
            for picking in invoice.picking_ids:
                picking_date = fields.Datetime.from_string(picking.date)
                references.append({
                    'DNRef': picking.name,
                    'PORef': (picking.sale_id.client_order_ref
                              or picking.sale_id.name),
                    'DNRefDate': picking_date and datetime.strftime(
                        picking_date, "%Y-%m-%d"),
                })
        else:
            orders = invoice.invoice_line_ids.mapped('sale_line_ids.order_id')
            date_invoice = fields.Date.from_string(invoice.date_invoice)
            for order in orders:
                references.append({
                    'DNRef': invoice.number,
                    'PORef': order.client_order_ref or order.name,
                    'DNRefDate': date_invoice and date.strftime(
                        date_invoice, "%Y-%m-%d"),
                })
        return references

    def _get_products_data(self, invoice):
        return [{
            'product': self._get_product_data(line),
            'taxes': self._get_product_taxes_data(line),
            'discounts': self._get_product_discounts_data(line),
        } for line in invoice.invoice_line_ids]

    def _get_product_data(self, line):
        return {
            'SupplierSKU': line.product_id.default_code,
            'Item': line.product_id.name,
            'Qty': str(line.quantity),
            'MU': line.uom_id.voxel_code,
            'UP': str(line.price_unit),
            'Total': str(line.quantity * line.price_unit),
        }

    def _get_product_discounts_data(self, line):
        taxes = []
        if line.discount:
            amount = round(
                line.price_subtotal / line.quantity - line.price_unit, 2)
            taxes.append({
                'Qualifier': line.discount > 0.0 and 'Descuento' or 'Cargo',
                'Type': line.discount > 0.0 and 'Comercial' or 'Otro',
                'Rate': str(line.discount),
                'Amount': str(amount),
            })
        return taxes

    def _get_product_taxes_data(self, line):
        taxes = []
        for tax in line.invoice_line_tax_ids:
            rate = tax.amount_type != 'group' and str(tax.amount) or False
            taxes.append({
                'Type': tax.voxel_tax_code,
                'Rate': rate,
            })
        return taxes

    def _get_taxes_data(self, invoice):
        taxes = []
        for tax_line in invoice.tax_line_ids:
            tax_obj = self.env['account.tax'].browse(tax_line.tax_id.id)
            taxes.append({
                'Type': tax_obj.voxel_tax_code,
                'Rate': str(tax_obj.amount),
                'Amount': str(tax_line['amount_total']),
            })
        return sorted(taxes, key=itemgetter('Type', 'Rate', 'Amount'))

    def _get_total_summary_data(self, invoice):
        return {
            'SubTotal': str(invoice.amount_untaxed),
            'Tax': str(invoice.amount_tax),
            'Total': str(invoice.amount_total),
        }
