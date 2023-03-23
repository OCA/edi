# -*- coding: utf-8 -*-
# © 2015-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_round
from openerp.exceptions import Warning as UserError
from lxml import etree
import logging
import mimetypes

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _name = 'account.invoice.import'
    _inherit = ['business.document.import']
    _description = 'Wizard to import supplier invoices/refunds'

    invoice_file = fields.Binary(
        string='PDF or XML Invoice', required=True)
    invoice_filename = fields.Char(string='Filename')
    state = fields.Selection([
        ('import', 'Import'),
        ('update', 'Update'),
        ], string='State', default="import")
    partner_id = fields.Many2one(
        'res.partner', string="Supplier", readonly=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', readonly=True)
    invoice_type = fields.Selection([
        ('in_invoice', 'Invoice'),
        ('in_refund', 'Refund'),
        ], string="Invoice or Refund", readonly=True)
    amount_untaxed = fields.Float(
        string='Total Untaxed', digits=dp.get_precision('Account'),
        readonly=True)
    amount_total = fields.Float(
        string='Total', digits=dp.get_precision('Account'),
        readonly=True)
    invoice_id = fields.Many2one(
        'account.invoice', string='Draft Supplier Invoice to Update')

    @api.model
    def parse_xml_invoice(self, xml_root):
        raise UserError(_(
            "This type of XML invoice is not supported. Did you install "
            "the module to support this type of file?"))

    @api.model
    def parse_pdf_invoice(self, file_data):
        '''This method must be inherited by additionnal modules with
        the same kind of logic as the account_bank_statement_import_*
        modules'''
        xml_files_dict = self.get_xml_files_from_pdf(file_data)
        for xml_filename, xml_root in xml_files_dict.iteritems():
            logger.info('Trying to parse XML file %s', xml_filename)
            try:
                parsed_inv = self.parse_xml_invoice(xml_root)
                return parsed_inv
            except:
                continue
        parsed_inv = self.fallback_parse_pdf_invoice(file_data)
        if not parsed_inv:
            raise UserError(_(
                "This type of PDF invoice is not supported. Did you install "
                "the module to support this type of file?"))
        return parsed_inv

    def fallback_parse_pdf_invoice(self, file_data):
        '''Designed to be inherited by the module
        account_invoice_import_invoice2data, to be sure the invoice2data
        technique is used after the electronic invoice modules such as
        account_invoice_import_zugferd
        '''
        return False

        # Dict to return:
        # {
        # 'currency': {
        #    'iso': 'EUR',
        #    'currency_symbol': u'€',  # The one or the other
        #    },
        # 'date': '2015-10-08',  # Must be a string
        # 'date_due': '2015-11-07',
        # 'date_start': '2015-10-01',  # for services over a period of time
        # 'date_end': '2015-10-31',
        # 'amount_untaxed': 10.0,  # < 0 for refunds
        # 'amount_tax': 2.0,  # provide amount_untaxed OR amount_tax
        # 'amount_total': 12.0,  # Total with taxes, must always be provided
        # 'partner': {
        #       'vat': 'FR25499247138',
        #       'email': 'support@browserstack.com',
        #       'name': 'Capitaine Train',
        #       },
        # 'partner': res.partner recordset,
        # 'invoice_number': 'I1501243',
        # 'description': 'TGV Paris-Lyon',
        # 'attachments': {'file1.pdf': base64data1, 'file2.pdf': base64data2},
        # 'chatter_msg': 'Note added in chatter of the invoice',
        # 'lines': [{
        #       'product': {
        #           'ean13': '4123456000021',
        #           'code': 'GZ250',
        #           },
        #       'name': 'Gelierzucker Extra 250g',
        #       'price_unit': 1.45, # price_unit without taxes always positive
        #       'qty': -2.0,  # < 0 when it's a refund
        #       'uom': {'unece_code': 'C62'},
        #       'taxes': [list of tax_dict],
        #       }],
        # }

    @api.model
    def _prepare_create_invoice_vals(self, parsed_inv):
        aio = self.env['account.invoice']
        ailo = self.env['account.invoice.line']
        company = self.env.user.company_id
        assert parsed_inv.get('amount_total'), 'Missing amount_total'
        partner = self._match_partner(
            parsed_inv['partner'], parsed_inv['chatter_msg'])
        partner = partner.commercial_partner_id
        currency = self._match_currency(
            parsed_inv.get('currency'), parsed_inv['chatter_msg'])
        vals = {
            'partner_id': partner.id,
            'currency_id': currency.id,
            'type': parsed_inv['type'],
            'company_id': company.id,
            'supplier_invoice_number':
            parsed_inv.get('invoice_number'),
            'date_invoice': parsed_inv.get('date'),
            'journal_id':
            aio.with_context(type='in_invoice')._default_journal().id,
            'invoice_line': [],
            'check_total': parsed_inv.get('amount_total'),
            }
        vals.update(aio.onchange_partner_id(
            'in_invoice', partner.id, company_id=company.id)['value'])
        # Force due date of the invoice
        if parsed_inv.get('date_due'):
            vals['date_due'] = parsed_inv.get('date_due')
        # Bank info
        if parsed_inv.get('iban'):
            iban = parsed_inv.get('iban').replace(' ', '')
            self._cr.execute(
                """SELECT id FROM res_partner_bank
                WHERE replace(acc_number, ' ', '')=%s
                AND state='iban'
                AND partner_id=%s
                """, (iban, vals['partner_id']))
            rpb_res = self._cr.fetchall()
            if rpb_res:
                vals['partner_bank_id'] = rpb_res[0][0]
            else:
                partner_bank = self.env['res.partner.bank'].create({
                    'partner_id': vals['partner_id'],
                    'state': 'iban',
                    'acc_number': parsed_inv['iban'],
                    'bank_bic': parsed_inv.get('bic'),
                    })
                vals['partner_bank_id'] = partner_bank.id
                parsed_inv['chatter_msg'].append(_(
                    "The bank account <b>IBAN %s</b> has been automatically "
                    "added on the supplier <b>%s</b>") % (
                    parsed_inv['iban'], partner.name))
        config = partner.invoice_import_id
        if config.invoice_line_method.startswith('1line'):
            if config.invoice_line_method == '1line_no_product':
                il_vals = {
                    'account_id': config.account_id.id,
                    'invoice_line_tax_id': config.tax_ids.ids or False,
                    'price_unit': parsed_inv.get('amount_untaxed'),
                    }
            elif config.invoice_line_method == '1line_static_product':
                product = config.static_product_id
                il_vals = ailo.product_id_change(
                    product.id, product.uom_id.id, type='in_invoice',
                    partner_id=partner.id,
                    fposition_id=partner.property_account_position.id,
                    company_id=company.id)['value']
                il_vals.update({
                    'product_id': product.id,
                    'price_unit': parsed_inv.get('amount_untaxed'),
                    })
            if config.label:
                il_vals['name'] = config.label
            elif parsed_inv.get('description'):
                il_vals['name'] = parsed_inv['description']
            elif not il_vals.get('name'):
                il_vals['name'] = _('MISSING DESCRIPTION')
            self.set_1line_price_unit_and_quantity(il_vals, parsed_inv)
            self.set_1line_start_end_dates(il_vals, parsed_inv)
            vals['invoice_line'].append((0, 0, il_vals))
        elif config.invoice_line_method.startswith('nline'):
            if not parsed_inv.get('lines'):
                raise UserError(_(
                    "You have selected a Multi Line method for this import "
                    "but Odoo could not extract/read any XML file inside "
                    "the PDF invoice."))
            if config.invoice_line_method == 'nline_no_product':
                static_vals = {
                    'account_id': config.account_id.id,
                    }
            elif config.invoice_line_method == 'nline_static_product':
                sproduct = config.static_product_id
                static_vals = ailo.product_id_change(
                    sproduct.id, sproduct.uom_id.id, type='in_invoice',
                    partner_id=partner.id,
                    fposition_id=partner.property_account_position.id,
                    company_id=company.id)['value']
                static_vals['product_id'] = sproduct.id
            else:
                static_vals = {}
            for line in parsed_inv['lines']:
                il_vals = static_vals.copy()
                if config.invoice_line_method == 'nline_auto_product':
                    product = self._match_product(
                        line['product'], parsed_inv['chatter_msg'],
                        seller=partner)
                    fposition_id = partner.property_account_position.id
                    il_vals.update(
                        ailo.product_id_change(
                            product.id, product.uom_id.id, type='in_invoice',
                            partner_id=partner.id,
                            fposition_id=fposition_id,
                            company_id=company.id)['value'])
                    il_vals['product_id'] = product.id
                elif config.invoice_line_method == 'nline_no_product':
                    taxes = self._match_taxes(
                        line.get('taxes'), parsed_inv['chatter_msg'])
                    il_vals['invoice_line_tax_id'] = taxes.ids
                if line.get('name'):
                    il_vals['name'] = line['name']
                elif not il_vals.get('name'):
                    il_vals['name'] = _('MISSING DESCRIPTION')
                uom = self._match_uom(
                    line.get('uom'), parsed_inv['chatter_msg'])
                il_vals['uos_id'] = uom.id
                il_vals.update({
                    'quantity': line['qty'],
                    'price_unit': line['price_unit'],
                    })
                vals['invoice_line'].append((0, 0, il_vals))
        # Write analytic account + fix syntax for taxes
        aacount_id = config.account_analytic_id.id or False
        for line in vals['invoice_line']:
            line_dict = line[2]
            if line_dict.get('invoice_line_tax_id'):
                line_dict['invoice_line_tax_id'] = [
                    (6, 0, line_dict['invoice_line_tax_id'])]
            if aacount_id:
                line_dict['account_analytic_id'] = aacount_id
        return vals

    @api.model
    def set_1line_price_unit_and_quantity(self, il_vals, parsed_inv):
        """For the moment, we only take into account the 'price_include'
        option of the first tax"""
        il_vals['quantity'] = 1
        il_vals['price_unit'] = parsed_inv.get('amount_total')
        if il_vals.get('invoice_line_tax_id'):
            first_tax = self.env['account.tax'].browse(
                il_vals['invoice_line_tax_id'][0])
            if not first_tax.price_include:
                il_vals['price_unit'] = parsed_inv.get('amount_untaxed')

    @api.model
    def set_1line_start_end_dates(self, il_vals, parsed_inv):
        """Only useful if you have installed the module account_cutoff_prepaid
        from https://github.com/OCA/account-closing"""
        fakeiline = self.env['account.invoice.line'].browse(False)
        if (
                parsed_inv.get('date_start') and
                parsed_inv.get('date_end') and
                hasattr(fakeiline, 'start_date') and
                hasattr(fakeiline, 'end_date')):
            il_vals['start_date'] = parsed_inv.get('date_start')
            il_vals['end_date'] = parsed_inv.get('date_end')

    @api.multi
    def parse_invoice(self):
        self.ensure_one()
        assert self.invoice_file, 'No invoice file'
        logger.info('Starting to import invoice %s', self.invoice_filename)
        file_data = self.invoice_file.decode('base64')
        parsed_inv = {}
        filetype = mimetypes.guess_type(self.invoice_filename)
        logger.debug('Invoice mimetype: %s', filetype)
        if filetype and filetype[0] == 'application/xml':
            try:
                xml_root = etree.fromstring(file_data)
            except:
                raise UserError(_(
                    "This XML file is not XML-compliant"))
            pretty_xml_string = etree.tostring(
                xml_root, pretty_print=True, encoding='UTF-8',
                xml_declaration=True)
            logger.debug('Starting to import the following XML file:')
            logger.debug(pretty_xml_string)
            parsed_inv = self.parse_xml_invoice(xml_root)
        # Fallback on PDF
        else:
            parsed_inv = self.parse_pdf_invoice(file_data)
        if 'attachments' not in parsed_inv:
            parsed_inv['attachments'] = {}
        parsed_inv['attachments'][self.invoice_filename] = self.invoice_file
        updated_parsed_inv = self.update_clean_parsed_inv(parsed_inv)
        return updated_parsed_inv

    @api.model
    def update_clean_parsed_inv(self, parsed_inv):
        prec_ac = self.env['decimal.precision'].precision_get('Account')
        prec_pp = self.env['decimal.precision'].precision_get('Product Price')
        prec_uom = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        if 'amount_tax' in parsed_inv and 'amount_untaxed' not in parsed_inv:
            parsed_inv['amount_untaxed'] =\
                parsed_inv['amount_total'] - parsed_inv['amount_tax']
        elif (
                'amount_untaxed' not in parsed_inv and
                'amount_tax' not in parsed_inv):
            # For invoices that never have taxes
            parsed_inv['amount_untaxed'] = parsed_inv['amount_total']
        if float_compare(
                parsed_inv['amount_total'], 0, precision_digits=prec_ac) == -1:
            parsed_inv['type'] = 'in_refund'
        else:
            parsed_inv['type'] = 'in_invoice'
        for entry in ['amount_untaxed', 'amount_total']:
            parsed_inv[entry] = float_round(
                parsed_inv[entry], precision_digits=prec_ac)
            if parsed_inv['type'] == 'in_refund':
                parsed_inv[entry] *= -1
        if parsed_inv.get('lines'):
            for line in parsed_inv['lines']:
                line['qty'] = float_round(
                    line['qty'], precision_digits=prec_uom)
                line['price_unit'] = float_round(
                    line['price_unit'], precision_digits=prec_pp)
                if parsed_inv['type'] == 'in_refund':
                    line['qty'] *= -1
        if 'chatter_msg' not in parsed_inv:
            parsed_inv['chatter_msg'] = []
        logger.debug('Resulf of invoice parsing parsed_inv=%s', parsed_inv)
        return parsed_inv

    @api.multi
    def import_invoice(self):
        """Method called by the button of the wizard (1st step)"""
        self.ensure_one()
        aio = self.env['account.invoice']
        iaao = self.env['ir.actions.act_window']
        parsed_inv = self.parse_invoice()
        partner = self._match_partner(
            parsed_inv['partner'], parsed_inv['chatter_msg'])
        partner = partner.commercial_partner_id
        currency = self._match_currency(
            parsed_inv.get('currency'), parsed_inv['chatter_msg'])
        parsed_inv['partner']['recordset'] = partner
        parsed_inv['currency']['recordset'] = currency
        # TODO Move to IF below : make sure we don't access self.partner_id
        self.write({
            'partner_id': partner.id,
            'invoice_type': parsed_inv['type'],
            'currency_id': currency.id,
            'amount_untaxed': parsed_inv['amount_untaxed'],
            'amount_total': parsed_inv['amount_total'],
            })
        if not partner.invoice_import_id:
            raise UserError(_(
                "Missing Invoice Import Configuration on partner %s")
                % partner.name)
        domain = [
            ('commercial_partner_id', '=', partner.id),
            ('type', '=', parsed_inv['type'])]
        existing_invs = aio.search(
            domain +
            [(
                'supplier_invoice_number',
                '=ilike',
                parsed_inv.get('invoice_number'))])
        if existing_invs:
            raise UserError(_(
                "This invoice already exists in Odoo. It's "
                "Supplier Invoice Number is '%s' and it's Odoo number "
                "is '%s'")
                % (parsed_inv.get('invoice_number'), existing_invs[0].number))
        draft_same_supplier_invs = aio.search(
            domain + [('state', '=', 'draft')])
        logger.debug('draft_same_supplier_invs=%s', draft_same_supplier_invs)
        if draft_same_supplier_invs:
            action = iaao.for_xml_id(
                'account_invoice_import',
                'account_invoice_import_action')
            default_invoice_id = False
            if len(draft_same_supplier_invs) == 1:
                default_invoice_id = draft_same_supplier_invs[0].id
            self.write({
                'state': 'update',
                'invoice_id': default_invoice_id,
            })
            action['res_id'] = self.id
            return action
        else:
            action = self.create_invoice()
            return action

    @api.multi
    def create_invoice(self):
        self.ensure_one()
        iaao = self.env['ir.actions.act_window']
        parsed_inv = self.parse_invoice()
        invoice = self._create_invoice(parsed_inv)
        invoice.message_post(_(
            "This invoice has been created automatically via file import"))
        action = iaao.for_xml_id('account', 'action_invoice_tree2')
        action.update({
            'view_mode': 'form,tree,calendar,graph',
            'views': False,
            'res_id': invoice.id,
            })
        return action

    @api.model
    def _create_invoice(self, parsed_inv):
        aio = self.env['account.invoice']
        vals = self._prepare_create_invoice_vals(parsed_inv)
        logger.debug('Invoice vals for creation: %s', vals)
        invoice = aio.create(vals)
        logger.info('Invoice ID %d created', invoice.id)
        invoice.button_reset_taxes()

        # Force tax amount if necessary
        prec = self.env['decimal.precision'].precision_get('Account')
        if (
                parsed_inv.get('amount_total') and
                parsed_inv.get('amount_untaxed') and
                float_compare(
                    invoice.amount_total,
                    parsed_inv['amount_total'],
                    precision_digits=prec)):
            if not invoice.tax_line:
                raise UserError(_(
                    "The total amount is different from the untaxed amount, "
                    "but no tax has been configured !"))
            initial_tax_amount = invoice.tax_line[0].amount
            tax_amount = parsed_inv['amount_total'] -\
                parsed_inv['amount_untaxed']
            invoice.tax_line[0].amount = tax_amount
            cur_symbol = invoice.currency_id.symbol
            invoice.message_post(
                'The total tax amount has been forced to %s %s '
                '(amount computed by Odoo was: %s %s).'
                % (tax_amount, cur_symbol, initial_tax_amount, cur_symbol))
        # Attach invoice and related documents
        if parsed_inv.get('attachments'):
            for filename, data_base64 in parsed_inv['attachments'].iteritems():
                self.env['ir.attachment'].create({
                    'name': filename,
                    'res_id': invoice.id,
                    'res_model': 'account.invoice',
                    'datas': data_base64,
                    'datas_fname': filename,
                    })
        for chatter_msg in parsed_inv['chatter_msg']:
            invoice.message_post(chatter_msg)
        return invoice

    @api.model
    def _prepare_update_invoice_vals(self, parsed_inv):
        vals = {
            'supplier_invoice_number':
            parsed_inv.get('invoice_number'),
            'date_invoice': parsed_inv.get('date'),
            'check_total': parsed_inv.get('amount_total'),
        }
        if parsed_inv.get('date_due'):
            vals['date_due'] = parsed_inv['date_due']
        return vals

    @api.multi
    def update_invoice(self):
        self.ensure_one()
        iaao = self.env['ir.actions.act_window']
        invoice = self.invoice_id
        if not invoice:
            raise UserError(_(
                'You must select a supplier invoice or refund to update'))
        parsed_inv = self.parse_invoice()
        currency = self._match_currency(
            parsed_inv.get('currency'), parsed_inv['chatter_msg'])
        if currency != invoice.currency_id:
            raise UserError(_(
                "The currency of the imported invoice (%s) is different from "
                "the currency of the existing invoice (%s)") % (
                currency.name, invoice.currency_id.name))
        # When invoice with embedded XML files will be more widely used,
        # we should also update invoice lines
        vals = self._prepare_update_invoice_vals(parsed_inv)
        logger.debug('Updating supplier invoice with vals=%s', vals)
        self.invoice_id.write(vals)
        # Attach invoice and related documents
        if parsed_inv.get('attachments'):
            for filename, data_base64 in parsed_inv['attachments'].iteritems():
                self.env['ir.attachment'].create({
                    'name': filename,
                    'res_id': invoice.id,
                    'res_model': 'account.invoice',
                    'datas': data_base64,
                    'datas_fname': filename,
                    })
        logger.info(
            'Supplier invoice ID %d updated via import of file %s',
            invoice.id, self.invoice_filename)
        invoice.message_post(_(
            "This invoice has been updated automatically via the import "
            "of file %s") % self.invoice_filename)
        action = iaao.for_xml_id('account', 'action_invoice_tree2')
        action.update({
            'view_mode': 'form,tree,calendar,graph',
            'views': False,
            'res_id': invoice.id,
            })
        return action
