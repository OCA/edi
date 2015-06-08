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
from datetime import datetime
from dateutil.relativedelta import relativedelta


logger = logging.getLogger(__name__)


class OvhInvoiceGet(models.TransientModel):
    _name = 'ovh.invoice.get'
    _description = 'Get OVH supplier invoices'

    def _default_from_date(self):
        today = datetime.today()
        return today + relativedelta(months=-1, day=1)

    auto_validate = fields.Boolean(string='Auto Validate')
    from_date = fields.Date(string='From Date', default=_default_from_date)
    attach_pdf = fields.Boolean(
        string='Attach PDF of OVH Invoice', default=True)

    @api.model
    def _prepare_invoice_vals(
            self, ovh_invoice_number, ovh_partner, ovh_account, res_iinfo):
        aio = self.env['account.invoice']
        company = self.env.user.company_id
        vals = {
            'partner_id': ovh_partner.id,
            'type': 'in_invoice',
            'company_id': company.id,
            'supplier_invoice_number': ovh_invoice_number,
            'origin': 'OVH SoAPI %s' % ovh_account.login,
            'date_invoice': res_iinfo.date[:10],
            'journal_id':
            aio.with_context(type='in_invoice')._default_journal().id,
            'invoice_line': [],
            'check_total': float(res_iinfo.finalprice),
            }
        vals.update(aio.onchange_partner_id(
            'in_invoice', ovh_partner.id, company_id=company.id)['value'])
        taxrate = float(res_iinfo.taxrate)  # =0.2 for 20%
        method = ovh_account.invoice_line_method
        il_fake = self.env['account.invoice.line'].browse([])
        if method == 'no_product':
            taxes = self.env['account.tax'].search([
                ('type_tax_use', '=', 'purchase'),
                ('amount', '=', taxrate),
                ('type', '=', 'percent'),
                ('price_include', '=', False),
                ])
            if len(taxes) < 1:
                raise Warning(_(
                    "Could not find proper purchase tax in Odoo "
                    "with a rate of %s %%") % (taxrate * 100))
            # TODO: we take the first one, which correspond to the
            # regular tax (the other ones are IMMO-20.0 & ACH_UE_ded.-20.0)
            tax_id = taxes[0].id
        elif method == 'product':
            products = self.env['product.product'].search([
                ('purchase_ok', '=', True),
                ('default_code', 'like', 'OVH-%')])
            if not products:
                raise Warning(_("No OVH product found in Odoo"))
            oproducts = {}
            # key = start of domain
            # value = product recordset
            for product in products:
                oproducts[product.default_code[4:]] = product
        for line in res_iinfo.details.item:
            if not line.baseprice:
                continue
            if method == 'no_product':
                il_vals = {
                    'account_id': ovh_account.account_id.id,
                    'account_analytic_id':
                    ovh_account.account_analytic_id.id or False,
                    'invoice_line_tax_id': [(6, 0, [tax_id])],
                    }
            elif method == 'product':
                assert line.domain, 'Missing domain on OVH invoice line'
                product = False
                for domain_start, oproduct in oproducts.iteritems():
                    if line.domain.startswith(domain_start):
                        product = oproduct
                        break
                if not product:
                    raise Warning(_(
                        'No OVH product matching domain %s')
                        % line.domain)
                il_vals = il_fake.product_id_change(
                    product.id, product.uom_id.id, type='in_invoice',
                    partner_id=ovh_partner.id,
                    fposition_id=ovh_partner.property_account_position.id,
                    currency_id=company.currency_id.id,
                    company_id=company.id)['value']
                if il_vals['invoice_line_tax_id']:
                    tax = self.env['account.tax'].browse(
                        il_vals['invoice_line_tax_id'][0])
                    if tax.amount != taxrate:
                        raise Warning(_(
                            "The OVH product with internal code %s "
                            "has a purchase tax '%s' (%s) with a rate %s "
                            "which is different from the rate "
                            "given by the OVH webservice (%s).") % (
                            product.default_code,
                            product.supplier_taxes_id[0].name,
                            product.supplier_taxes_id[0].description,
                            product.supplier_taxes_id[0].amount,
                            taxrate))
                il_vals.update({
                    'invoice_line_tax_id':
                    [(6, 0, il_vals['invoice_line_tax_id'])],
                    'product_id': product.id,
                    })
            il_vals.update({
                'quantity': float(line.quantity),
                'price_unit': float(line.baseprice),
                'name': line.description,
                })
            if line.start and line.end:
                start_date_str = line.start[:10]
                end_date_str = line.end[:10]
                end_date_dt = fields.Date.from_string(end_date_str)
                end_date_dt -= relativedelta(days=1)
                end_date_str = fields.Date.to_string(end_date_dt)
                il_vals['name'] = _('%s du %s au %s') % (
                    line.description, start_date_str, end_date_str)
                if (
                        hasattr(il_fake, 'start_date') and
                        hasattr(il_fake, 'end_date')):
                    il_vals['start_date'] = start_date_str
                    il_vals['end_date'] = end_date_str
            vals['invoice_line'].append((0, 0, il_vals))
        return vals

    def ovh_invoice_attach_pdf(
            self, invoice, ovh_invoice_number, invoice_password):
        logger.info(
            'Starting to download PDF of OVH invoice %s', ovh_invoice_number)
        rpdf = requests.get(
            'https://www.ovh.com/cgi-bin/order/facture.pdf'
            '?reference=%s&passwd=%s'
            % (ovh_invoice_number, invoice_password))
        logger.info(
            'OVH invoice PDF download HTTP code: %s', rpdf.status_code)
        if rpdf.status_code == 200:
            self.env['ir.attachment'].create({
                'name': 'OVH_invoice_%s.pdf' % ovh_invoice_number,
                'res_id': invoice.id,
                'res_model': 'account.invoice',
                'datas': base64.encodestring(rpdf.content),
                })
            logger.info(
                'Attachement created on OVH invoice %s', ovh_invoice_number)
            invoice.message_post(_(
                '<p>The PDF file of the OVH invoice has been '
                'successfully downloaded. You can get it in '
                'the attachments.'))
        else:
            logger.warning(
                'Could not download the PDF of the OVH invoice %s. '
                'HTTP error %d', ovh_invoice_number, rpdf.status_code)
            invoice.message_post(
                _('Failed to download the PDF file of the OVH '
                    'invoice (HTTP error %d') % rpdf.status_code)

    @api.multi
    def get(self):
        self.ensure_one()
        aio = self.env['account.invoice']
        soap = WSDL.Proxy('https://www.ovh.com/soapi/soapi-re-1.63.wsdl')
        user = self.env.user
        if not user.company_id.country_id:
            raise Warning(
                _('Missing country on company %s') % user.company_id.name)
        country_code = user.company_id.country_id.code.lower()
        partner = self.env['res.partner'].search([
            ('vat', '=', 'FR22424761419'),
            ('supplier', '=', 'True')])
        if not partner:
            raise Warning(
                _("Couldn't find the supplier OVH. Make sure you have "
                    "a supplier OVH with VAT number FR22424761419."))
        ovh_partner = partner[0]

        invoices = aio.browse(False)
        ovh_accounts = self.env['ovh.account'].search(
            [('company_id', '=', user.company_id.id)])
        for ovh_account in ovh_accounts:
            logger.info(
                'Opening SOAP session to OVH with account %s',
                ovh_account.login)
            session = soap.login(
                ovh_account.login,
                ovh_account.password,
                country_code, 0)
            logger.info(
                'Starting OVH soAPI query billingInvoiceList (account %s)',
                ovh_account.login)
            res_ilist = soap.billingInvoiceList(session)

            oinv_numbers = []
            for oinv in res_ilist.item:
                if self.from_date:
                    oinv_date = oinv.date[:10]
                    if oinv_date < self.from_date:
                        continue
                logger.info(
                    'billingInvoiceList: OVH invoice number %s (account %s)',
                    oinv.billnum, ovh_account.login)
                oinv_numbers.append(oinv.billnum)
            for oinv_num in oinv_numbers:
                # Check if this invoice is not already in the system
                existing_inv = aio.search([
                    ('type', '=', 'in_invoice'),
                    ('partner_id', '=', ovh_partner.id),
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
                res_iinfo = soap.billingInvoiceInfo(
                    session, oinv_num, ovh_account.password, country_code)
                vals = self._prepare_invoice_vals(
                    oinv_num, ovh_partner, ovh_account, res_iinfo)
                invoice = aio.create(vals)
                invoice.button_reset_taxes()
                invoices += invoice
                invoice.message_post(_(
                    '<p>This OVH invoice has been downloaded automatically '
                    'via the SoAPI with OVH account %s.</p>'
                    '<ul>'
                    '<li>Total without taxes: %s</li>'
                    '<li>Total VAT: %s</li>'
                    '<li>Total with taxes: %s</li>'
                    '</ul>')
                    % (ovh_account.login, res_iinfo.baseprice, res_iinfo.tax,
                        res_iinfo.finalprice))
                # Attach PDF
                if self.attach_pdf:
                    self.ovh_invoice_attach_pdf(
                        invoice, oinv_num, res_iinfo.password)
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
