# -*- encoding: utf-8 -*-
##############################################################################
#
#    OVH Supplier Invoice module for Odoo
#    Copyright (C) 2015 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, workflow, _
from openerp.exceptions import Warning
from SOAPpy import WSDL
import requests
import logging
import base64

# TODO : setup a dedicated obj to store login & passwd
# By the way, should be store the pwd in odoo or ask it on the fly
LOGIN = 'login-ovh'
PWD = 'xxxxxxxxx'
logger = logging.getLogger(__name__)


class OvhInvoiceGet(models.TransientModel):
    _name = 'ovh.invoice.get'
    _description = 'Get OVH supplier invoices'

    auto_validate = fields.Boolean(string='Auto Validate')
    from_date = fields.Date(string='From Date')

    @api.model
    def _prepare_invoice_vals(
            self, ovh_invoice_number, ovh_partner_id, res_iinfo):
        aio = self.env['account.invoice']
        company_id = self.env.user.company_id.id
        vals = {
            'partner_id': ovh_partner_id,
            'type': 'in_invoice',
            'company_id': company_id,
            'supplier_invoice_number': ovh_invoice_number,
            'origin': 'OVH SoAPI',
            'date_invoice': res_iinfo.date[:10],
            'journal_id':
            aio.with_context(type='in_invoice')._default_journal().id,
            'invoice_line': [],
            'check_total': float(res_iinfo.finalprice),
            }
        vals.update(aio.onchange_partner_id(
            'in_invoice', ovh_partner_id, company_id=company_id)['value'])
        taxes = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'),
            ('amount', '=', float(res_iinfo.taxrate)),
            ('type', '=', 'percent'),
            ('price_include', '=', False),
            ])
        assert len(taxes) > 1, 'Could not find proper tax'
        tax_id = taxes[0].id  # Too bad
        for line in res_iinfo.details.item:
            if line.start and line.end:
                name = '%s du %s au %s' % (
                    line.description, line.start, line.end)
            else:
                name = line.description
            il_vals = {
                'quantity': float(line.quantity),
                'price_unit': float(line.baseprice),
                'invoice_line_tax_id': [(6, 0, [tax_id])],
                'name': name,
                }
            vals['invoice_line'].append((0, 0, il_vals))
        return vals

    @api.multi
    def get(self):
        self.ensure_one()
        aio = self.env['account.invoice']
        logger.info('Opening SOAP session to OVH')
        soap = WSDL.Proxy('https://www.ovh.com/soapi/soapi-re-1.63.wsdl')
        # TODO : don't hardcode 'fr'
        session = soap.login(LOGIN, PWD, 'fr', 0)
        logger.info('Starting OVH soAPI query billingInvoiceList')
        res_ilist = soap.billingInvoiceList(session)
        oinv_numbers = []
        partner = self.env['res.partner'].search([
            ('vat', '=', 'FR22424761419'),
            ('supplier', '=', 'True')])
        if not partner:
            raise Warning(
                _("Couldn't find the supplier OVH. Make sure you have "
                    "a supplier OVH with VAT number FR22424761419."))
        ovh_partner_id = partner[0].id

        for oinv in res_ilist.item:
            if self.from_date:
                oinv_date = oinv.date[:10]
                if oinv_date < self.from_date:
                    continue
            logger.info(
                'billingInvoiceList: OVH invoice number %s',
                oinv.billnum)
            oinv_numbers.append(oinv.billnum)
        invoices = aio.browse(False)
        for oinv_num in oinv_numbers:
            # Check if this invoice is not already in the system
            existing_inv = aio.search([
                ('type', '=', 'in_invoice'),
                ('partner_id', '=', ovh_partner_id),
                ('supplier_invoice_number', '=', oinv_num),
                ])
            if existing_inv:
                logger.warning(
                    'The OVH invoice number %s already exists in Odoo',
                    oinv_num)
                continue
            logger.info(
                'Starting OVH soAPI query billingInvoiceInfo on OVH '
                'invoice number %s', oinv_num)
            res_iinfo = soap.billingInvoiceInfo(session, oinv_num, PWD, 'fr')
            vals = self._prepare_invoice_vals(
                oinv_num, ovh_partner_id, res_iinfo)
            invoice = aio.create(vals)
            invoice.button_reset_taxes()
            invoices += invoice
            invoice.message_post(
                'This invoice has been downloaded automatically '
                'via the SoAPI of OVH.\nTotal without taxes: %s\n'
                'Total VAT: %s\n Total with taxes: %s'
                % (res_iinfo.baseprice, res_iinfo.tax, res_iinfo.finalprice))
            # Attach PDF
            logger.info('Starting to download PDF of OVH invoice %s', oinv_num)
            rpdf = requests.get(
                'https://www.ovh.com/cgi-bin/order/facture.pdf'
                '?reference=%s&passwd=%s'
                % (oinv_num, res_iinfo.password))
            logger.info(
                'OVH invoice PDF download HTTP code: %s', rpdf.status_code)
            if rpdf.status_code == 200:
                self.env['ir.attachment'].create({
                    'name': 'OVH_invoice_%s.pdf' % oinv_num,
                    'res_id': invoice.id,
                    'res_model': aio._name,
                    'datas': base64.encodestring(rpdf.content),
                    })
                logger.info('Attachement created on OVH invoice %s', oinv_num)
            # Validate invoice
            if self.auto_validate:
                workflow.trg_validate(
                    self._uid, aio._name, invoice.id,
                    'invoice_open', self._cr)

        action = self.env['ir.actions.act_window'].for_xml_id(
            'account', 'action_invoice_tree2')
        action.update({
            'view_mode': 'tree,form,calendar,graph',
            'domain': "[('id', 'in', %s)]" % invoices.ids,
            'views': False,
            'nodestroy': False,
            })
        return action
