# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.tools import float_compare
from odoo.addons.base_iban.models.res_partner_bank import validate_iban
from odoo.exceptions import UserError
from lxml import etree
from io import BytesIO
import mimetypes
from urllib.parse import urlparse
import logging
logger = logging.getLogger(__name__)

try:
    import PyPDF2
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BusinessDocumentImport(models.AbstractModel):
    _name = 'business.document.import'
    _description = 'Common methods to import business documents'

    @api.model
    def user_error_wrap(self, error_msg):
        assert error_msg
        prefix = self._context.get('error_prefix')
        if prefix and isinstance(prefix, str):
            error_msg = '%s\n%s' % (prefix, error_msg)
        raise UserError(error_msg)

    @api.model
    def _strip_cleanup_dict(self, match_dict):
        if match_dict:
            for key, value in match_dict.items():
                if value and isinstance(value, str):
                    match_dict[key] = value.strip()
            if match_dict.get('country_code'):
                match_dict['country_code'] = match_dict['country_code'].upper()
            if match_dict.get('state_code'):
                match_dict['state_code'] = match_dict['state_code'].upper()

    @api.model
    def _match_partner(
            self, partner_dict, chatter_msg, partner_type='supplier'):
        """Example:
        partner_dict = {
            'country_code': 'FR',
            'state_code': False,
            'vat': 'FR12448890432',
            'email': 'roger.lemaire@akretion.com',
            'website': 'www.akretion.com',
            'name': 'Akretion France',
            'ref': 'C1242',
            'phone': '01.41.98.12.42',
            }
        The key 'phone' is used by the module
        base_phone_business_document_import
        """
        company = self.env.user.company_id
        if hasattr(self, 'company_id') and self.company_id:
            company = self.company_id
        rpo = self.env['res.partner']
        self._strip_cleanup_dict(partner_dict)
        if partner_dict.get('recordset'):
            return partner_dict['recordset']
        if partner_dict.get('id'):
            return rpo.browse(partner_dict['id'])
        if partner_type == 'supplier':
            domain = [('supplier', '=', True)]
            partner_type_label = _('supplier')
        elif partner_type == 'customer':
            domain = [('customer', '=', True)]
            partner_type_label = _('customer')
        else:
            domain = []
            partner_type_label = _('partner')
        country = False
        if partner_dict.get('country_code'):
            countries = self.env['res.country'].search([
                ('code', '=', partner_dict['country_code'])])
            if countries:
                country = countries[0]
                domain += [
                    '|',
                    ('country_id', '=', False),
                    ('country_id', '=', country.id)]
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned '%s' as "
                    "country code. But there are no country with that code "
                    "in Odoo.") % partner_dict['country_code'])
        if country and partner_dict.get('state_code'):
            states = self.env['res.country.state'].search([
                ('code', '=', partner_dict['state_code']),
                ('country_id', '=', country.id)])
            if states:
                domain += [
                    '|',
                    ('state_id', '=', False),
                    ('state_id', '=', states[0].id)]
        if partner_dict.get('vat'):
            vat = partner_dict['vat'].replace(' ', '').upper()
            # use base_vat_sanitized
            partners = rpo.search(
                domain + [
                    ('parent_id', '=', False),
                    ('sanitized_vat', '=', vat),
                    '|',
                    ('company_id', '=', False),
                    ('company_id', '=', company.id)])
            if partners:
                return partners[0]
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned '%s' as "
                    "%s VAT number. But there are no %s "
                    "with this VAT number in Odoo.")
                    % (vat, partner_type_label, partner_type_label))
        # Hook to plug alternative matching methods
        partner = self._hook_match_partner(
            partner_dict, chatter_msg, domain, partner_type_label)
        if partner:
            return partner
        website_domain = False
        email_domain = False
        if partner_dict.get('email') and '@' in partner_dict['email']:
            partners = rpo.search(
                domain + [('email', '=ilike', partner_dict['email'])])
            if partners:
                return partners[0]
            else:
                email_domain = partner_dict['email'].split('@')[1]
        if partner_dict.get('website'):
            urlp = urlparse(partner_dict['website'])
            netloc = urlp.netloc
            if not urlp.scheme and not netloc:
                netloc = urlp.path
            if netloc and len(netloc.split('.')) >= 2:
                website_domain = '.'.join(netloc.split('.')[-2:])
        if website_domain or email_domain:
            partner_domain = website_domain or email_domain
            partners = rpo.search(
                domain +
                [('website', '=ilike', '%' + partner_domain + '%')])
            # I can't search on email addresses with
            # email_domain because of the emails such as
            # @gmail.com, @yahoo.com that may match random partners
            if not partners and website_domain:
                partners = rpo.search(
                    domain +
                    [('email', '=ilike', '%@' + website_domain)])
            if partners:
                chatter_msg.append(_(
                    "The %s has been identified by the domain name '%s' "
                    "so please check carefully that the %s is correct.") % (
                        partner_type_label,
                        partner_domain,
                        partner_type_label))
                return partners[0]
        if partner_dict.get('ref'):
            partners = rpo.search(
                domain + [('ref', '=', partner_dict['ref'])])
            if partners:
                return partners[0]
        if partner_dict.get('name'):
            partners = rpo.search(
                domain + [('name', '=ilike', partner_dict['name'])])
            if partners:
                return partners[0]
        raise self.user_error_wrap(_(
            "Odoo couldn't find any %s corresponding to the following "
            "information extracted from the business document:\n"
            "Name: %s\n"
            "VAT number: %s\n"
            "Reference: %s\n"
            "E-mail: %s\n"
            "Website: %s\n"
            "State code: %s\n"
            "Country code: %s\n")
            % (
                partner_type_label,
                partner_dict.get('name'),
                partner_dict.get('vat'),
                partner_dict.get('ref'),
                partner_dict.get('email'),
                partner_dict.get('website'),
                partner_dict.get('state_code'),
                partner_dict.get('country_code'),
                ))

    @api.model
    def _hook_match_partner(
            self, partner_dict, chatter_msg, domain, partner_type_label):
        return False

    @api.model
    def _match_shipping_partner(self, shipping_dict, partner, chatter_msg):
        """Example:
        shipping_dict = {
            'partner': {
                'email': 'contact@akretion.com',
                'name': 'Akretion France',
                },
            'address': {
                'zip': '69100',
                'country_code': 'FR',
                },
            }
        The partner argument is a bit special: it is a fallback in case
        shipping_dict['partner'] = {}
        """
        rpo = self.env['res.partner']
        if shipping_dict.get('partner'):
            partner = self._match_partner(
                shipping_dict['partner'], chatter_msg, partner_type=False)
        domain = [('parent_id', '=', partner.id)]
        address_dict = shipping_dict['address']
        self._strip_cleanup_dict(address_dict)
        country = False
        if address_dict.get('country_code'):
            countries = self.env['res.country'].search([
                ('code', '=', address_dict['country_code'])])
            if countries:
                country = countries[0]
                domain += [
                    '|',
                    ('country_id', '=', False),
                    ('country_id', '=', country.id)]
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned '%s' as "
                    "country code. But there are no country with that code "
                    "in Odoo.") % address_dict['country_code'])
        if country and address_dict.get('state_code'):
            states = self.env['res.country.state'].search([
                ('code', '=', address_dict['state_code']),
                ('country_id', '=', country.id)])
            if states:
                domain += [
                    '|',
                    ('state_id', '=', False),
                    ('state_id', '=', states[0].id)]
        if address_dict.get('zip'):
            domain.append(('zip', '=', address_dict['zip']))
            # sanitize ZIP ?
        partners = rpo.search(domain + [('type', '=', 'delivery')])
        if partners:
            partner = partners[0]
        else:
            partners = rpo.search(domain)
            if partners:
                partner = partners[0]
        return partner

    @api.model
    def _match_partner_bank(
            self, partner, iban, bic, chatter_msg, create_if_not_found=False):
        assert iban, 'iban is a required arg'
        assert partner, 'partner is a required arg'
        partner = partner.commercial_partner_id
        iban = iban.replace(' ', '').upper()
        rpbo = self.env['res.partner.bank']
        rbo = self.env['res.bank']
        try:
            validate_iban(iban)
        except Exception as e:
            chatter_msg.append(_(
                "IBAN <b>%s</b> is not valid, so it has been ignored.") % iban)
            return False
        bankaccounts = rpbo.search([
            ('acc_type', '=', 'iban'),
            ('sanitized_acc_number', '=', iban),
            ('partner_id', '=', partner.id)])
        if bankaccounts:
            return bankaccounts[0]
        elif create_if_not_found:
            bank_id = False
            if bic:
                bic = bic.replace(' ', '').upper()
                banks = rbo.search([('bic', '=', bic)])
                if banks:
                    bank_id = banks[0].id
                else:
                    bank = rbo.create({
                        'bic': bic,
                        'name': bic,  # TODO: see if we could do better
                    })
                    bank_id = bank.id
            partner_bank = rpbo.create({
                'partner_id': partner.id,
                'acc_number': iban,
                'bank_id': bank_id,
            })
            chatter_msg.append(_(
                "The bank account <b>IBAN %s</b> has been automatically "
                "added on the supplier <b>%s</b>") % (
                iban, partner.name))
            return partner_bank

    @api.model
    def _match_product(self, product_dict, chatter_msg, seller=False):
        """Example:
        product_dict = {
            'barcode': '5449000054227',
            'code': 'COCA1L',
            }
        """
        ppo = self.env['product.product']
        self._strip_cleanup_dict(product_dict)
        if product_dict.get('recordset'):
            return product_dict['recordset']
        if product_dict.get('id'):
            return ppo.browse(product_dict['id'])
        if product_dict.get('barcode'):
            products = ppo.search([
                ('barcode', '=', product_dict['barcode'])])
            if products:
                return products[0]
        if product_dict.get('code'):
            products = ppo.search([
                '|',
                ('barcode', '=', product_dict['code']),
                ('default_code', '=', product_dict['code'])])
            if products:
                return products[0]
            # WARNING: Won't work for multi-variant products
            # because product.supplierinfo is attached to product template
            if seller:
                sinfo = self.env['product.supplierinfo'].search([
                    ('name', '=', seller.id),
                    ('product_code', '=', product_dict['code']),
                ])
                if (
                        sinfo and
                        sinfo[0].product_tmpl_id.product_variant_ids and
                        len(
                        sinfo[0].product_tmpl_id.product_variant_ids) == 1
                ):
                    return sinfo[0].product_tmpl_id.product_variant_ids[0]
        raise self.user_error_wrap(_(
            "Odoo couldn't find any product corresponding to the "
            "following information extracted from the business document: "
            "Barcode: %s\n"
            "Product code: %s\n"
            "Supplier: %s\n") % (
                product_dict.get('barcode'),
                product_dict.get('code'),
                seller and seller.name or 'None'))

    @api.model
    def _match_currency(self, currency_dict, chatter_msg):
        """Example:
        currency_dict = {
            'iso': 'USD',  # If we have ISO, no need to have more keys
            'symbol': '$',
            'country_code': 'US',
            }
        """
        if not currency_dict:
            currency_dict = {}
        rco = self.env['res.currency']
        self._strip_cleanup_dict(currency_dict)
        if currency_dict.get('recordset'):
            return currency_dict['recordset']
        if currency_dict.get('id'):
            return rco.browse(currency_dict['id'])
        if currency_dict.get('iso'):
            currency_iso = currency_dict['iso'].upper()
            currencies = rco.search(
                [('name', '=', currency_iso)])
            if currencies:
                return currencies[0]
            else:
                raise self.user_error_wrap(_(
                    "The analysis of the business document returned '%s' as "
                    "the currency ISO code. But there are no currency "
                    "with that code in Odoo.") % currency_iso)
        if currency_dict.get('symbol'):
            currencies = rco.search(
                [('symbol', '=', currency_dict['symbol'])])
            if len(currencies) == 1:
                return currencies[0]
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned '%s' as "
                    "the currency symbol. But there are none or several "
                    "currencies with that symbol in Odoo.")
                    % currency_dict['symbol'])
        if currency_dict.get('iso_or_symbol'):
            currencies = rco.search([
                '|',
                ('name', '=', currency_dict['iso_or_symbol'].upper()),
                ('symbol', '=', currency_dict['iso_or_symbol'])])
            if currencies:
                return currencies[0]
            else:
                raise self.user_error_wrap(_(
                    "The analysis of the business document returned '%s' as "
                    "the currency symbol or ISO code. But there are no "
                    "currency with the symbol nor ISO code in Odoo.")
                    % currency_dict['iso_or_symbol'])
        if currency_dict.get('country_code'):
            country_code = currency_dict['country_code']
            countries = self.env['res.country'].search([
                ('code', '=', country_code)])
            if countries:
                country = countries[0]
                if country.currency_id:
                    return country.currency_id
                else:
                    raise self.user_error_wrap(_(
                        "The analysis of the business document returned '%s' "
                        "as the country code to find the related currency. "
                        "But the country '%s' doesn't have any related "
                        "currency configured in Odoo.")
                        % (country_code, country.name))
            else:
                raise self.user_error_wrap(_(
                    "The analysis of the business document returned '%s' "
                    "as the country code to find the related currency. "
                    "But there is no country with that code in Odoo.")
                    % country_code)
        company_cur = self.env.user.company_id.currency_id
        chatter_msg.append(_(
            'No currency specified, so Odoo used the company currency (%s)')
            % company_cur.name)
        return company_cur

    @api.model
    def _match_uom(self, uom_dict, chatter_msg, product=False):
        """Example:
        uom_dict = {
            'unece_code': 'LTR',
            'name': 'Liter',
            }
        """
        puo = self.env['product.uom']
        if not uom_dict:
            uom_dict = {}
        self._strip_cleanup_dict(uom_dict)
        if uom_dict.get('recordset'):
            return uom_dict['recordset']
        if uom_dict.get('id'):
            return puo.browse(uom_dict['id'])
        if uom_dict.get('unece_code'):
            # Map NIU to Unit
            if uom_dict['unece_code'] == 'NIU':
                uom_dict['unece_code'] = 'C62'
            uoms = puo.search([
                ('unece_code', '=', uom_dict['unece_code'])])
            if uoms:
                return uoms[0]
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned '%s' "
                    "as the unit of measure UNECE code, but there is no "
                    "unit of measure with that UNECE code in Odoo. Please "
                    "check the configuration of the units of measures in "
                    "Odoo.") % uom_dict['unece_code'])
        if uom_dict.get('name'):
            uoms = puo.search([
                ('name', '=ilike', uom_dict['name'] + '%')])
            if uoms:
                return uoms[0]
        if product:
            return product.uom_id
        chatter_msg.append(_(
            "<p>Odoo couldn't find any unit of measure corresponding to the "
            "following information extracted from the business document:</p>"
            "<ul><li>UNECE code: %s</li>"
            "<li>Name of the unit of measure: %s</li></ul>"
            "<p>So the unit of measure 'Unit(s)' has been used. <em>You may "
            "have to change it manually.</em></p>")
            % (uom_dict.get('unece_code'), uom_dict.get('name')))
        return self.env.ref('product.product_uom_unit')

    @api.model
    def _match_taxes(
            self, taxes_list, chatter_msg,
            type_tax_use='purchase', price_include=False):
        """taxes_list must be a list of tax_dict"""
        taxes_recordset = self.env['account.tax'].browse(False)
        for tax_dict in taxes_list:
            taxes_recordset += self._match_tax(
                tax_dict, chatter_msg, type_tax_use=type_tax_use,
                price_include=price_include)
        return taxes_recordset

    @api.model
    def _match_tax(
            self, tax_dict, chatter_msg,
            type_tax_use='purchase', price_include=False):
        """Example:
        tax_dict = {
            'amount_type': 'percent',  # required param, 'fixed' or 'percent'
            'amount': 20.0,  # required
            'unece_type_code': 'VAT',
            'unece_categ_code': 'S',
            'unece_due_date_code': '432',
            }
        """
        ato = self.env['account.tax']
        self._strip_cleanup_dict(tax_dict)
        if tax_dict.get('recordset'):
            return tax_dict['recordset']
        if tax_dict.get('id'):
            return ato.browse(tax_dict['id'])
        domain = []
        prec = self.env['decimal.precision'].precision_get('Account')
        # we should not use the Account prec directly, but...
        if type_tax_use == 'purchase':
            domain.append(('type_tax_use', '=', 'purchase'))
        elif type_tax_use == 'sale':
            domain.append(('type_tax_use', '=', 'sale'))
        if price_include is False:
            domain.append(('price_include', '=', False))
        elif price_include is True:
            domain.append(('price_include', '=', True))
        # with the code above, if you set price_include=None, it will
        # won't depend on the value of the price_include parameter
        assert tax_dict.get('amount_type') in ['fixed', 'percent'],\
            'bad tax type'
        assert 'amount' in tax_dict, 'Missing amount key in tax_dict'
        domain.append(('amount_type', '=', tax_dict['amount_type']))
        if tax_dict.get('unece_type_code'):
            domain.append(
                ('unece_type_code', '=', tax_dict['unece_type_code']))
        if tax_dict.get('unece_categ_code'):
            domain.append(
                ('unece_categ_code', '=', tax_dict['unece_categ_code']))
        if tax_dict.get('unece_due_date_code'):
            domain += [
                '|',
                ('unece_due_date_code', '=', tax_dict['unece_due_date_code']),
                ('unece_due_date_code', '=', False)]
        taxes = ato.search(domain, order='unece_due_date_code')
        for tax in taxes:
            tax_amount = tax.amount
            if not float_compare(
                    tax_dict['amount'], tax_amount, precision_digits=prec):
                return tax
        raise self.user_error_wrap(_(
            "Odoo couldn't find any tax with 'Tax Application' = '%s' "
            "and 'Tax Included in Price' = '%s' which correspond to the "
            "following information extracted from the business document:\n"
            "UNECE Tax Type code: %s\n"
            "UNECE Tax Category code: %s\n"
            "Tax amount: %s %s") % (
                type_tax_use,
                price_include,
                tax_dict.get('unece_type_code'),
                tax_dict.get('unece_categ_code'),
                tax_dict['amount'],
                tax_dict['amount_type'] == 'percent' and '%' or _('(fixed)')))

    def compare_lines(
            self, existing_lines, import_lines, chatter_msg,
            qty_precision=None, price_precision=None, seller=False):
        """ Example:
        existing_lines = [{
            'product': odoo_recordset,
            'name': 'USB Adapter',
            'qty': 1.5,
            'price_unit': 23.43,  # without taxes
            'uom': uom,
            'line': recordset,
            # Add taxes
            }]
        import_lines = [{
            'product': {
                'barcode': '2100002000003',
                'code': 'EAZY1',
                },
            'quantity': 2,
            'price_unit': 12.42,  # without taxes
            'uom': {'unece_code': 'C62'},
            }]

        Result of the method:
        {
            'to_remove': line_multirecordset,
            'to_add': [
                {
                    'product': recordset1,
                    'uom', recordset,
                    'import_line': {import dict},
                    # We provide product and uom as recordset to avoid the
                    # need to compute a second match
                ]
            'to_update': {
                'line1_recordset': {'qty': [1, 2], 'price_unit': [4.5, 4.6]},
                # qty must be updated from 1 to 2
                # price must be updated from 4.5 to 4.6
                'line2_recordset': {'qty': [12, 13]},
                # only qty must be updated
                }
        }

        The check existing_currency == import_currency must be done before
        the call to compare_lines()
        """
        dpo = self.env['decimal.precision']
        if qty_precision is None:
            qty_precision = dpo.precision_get('Product Unit of Measure')
        if price_precision is None:
            price_precision = dpo.precision_get('Product Price')
        existing_lines_dict = {}
        for eline in existing_lines:
            if not eline.get('product'):
                chatter_msg.append(_(
                    "The existing line '%s' doesn't have any product, "
                    "so <b>the lines haven't been updated</b>.")
                    % eline.get('name'))
                return False
            if eline['product'] in existing_lines_dict:
                chatter_msg.append(_(
                    "The product '%s' is used on several existing "
                    "lines, so <b>the lines haven't been updated</b>.")
                    % eline['product'].display_name)
                return False
            existing_lines_dict[eline['product']] = eline
        unique_import_products = []
        res = {
            'to_remove': False,
            'to_add': [],
            'to_update': {},
        }
        for iline in import_lines:
            if not iline.get('product'):
                chatter_msg.append(_(
                    "One of the imported lines doesn't have any product, "
                    "so <b>the lines haven't been updated</b>."))
                return False
            product = self._match_product(
                iline['product'], chatter_msg, seller=seller)
            uom = self._match_uom(iline.get('uom'), chatter_msg, product)
            if product in unique_import_products:
                chatter_msg.append(_(
                    "The product '%s' is used on several imported lines, "
                    "so <b>the lines haven't been updated</b>.")
                    % product.display_name)
                return False
            unique_import_products.append(product)
            if product in existing_lines_dict:
                if uom != existing_lines_dict[product]['uom']:
                    chatter_msg.append(_(
                        "For product '%s', the unit of measure is %s on the "
                        "existing line, but it is %s on the imported line. "
                        "We don't support this scenario for the moment, so "
                        "<b>the lines haven't been updated</b>.") % (
                            product.display_name,
                            existing_lines_dict[product]['uom'].name,
                            uom.name,
                    ))
                    return False
                # used for to_remove
                existing_lines_dict[product]['import'] = True
                oline = existing_lines_dict[product]['line']
                res['to_update'][oline] = {}
                if float_compare(
                        iline['qty'],
                        existing_lines_dict[product]['qty'],
                        precision_digits=qty_precision):
                    res['to_update'][oline]['qty'] = [
                        existing_lines_dict[product]['qty'],
                        iline['qty']]
                if (
                        'price_unit' in iline and
                        float_compare(
                            iline['price_unit'],
                            existing_lines_dict[product]['price_unit'],
                            precision_digits=price_precision)):
                    res['to_update'][oline]['price_unit'] = [
                        existing_lines_dict[product]['price_unit'],
                        iline['price_unit']]
            else:
                res['to_add'].append({
                    'product': product,
                    'uom': uom,
                    'import_line': iline,
                })
        for exiting_dict in existing_lines_dict.values():
            if not exiting_dict.get('import'):
                if res['to_remove']:
                    res['to_remove'] += exiting_dict['line']
                else:
                    res['to_remove'] = exiting_dict['line']
        return res

    def _prepare_account_speed_dict(self):
        res = self.env['account.account'].search_read([
            ('company_id', '=', self.env.user.company_id.id),
            ('deprecated', '=', False)], ['code'])
        speed_dict = {}
        for l in res:
            speed_dict[l['code'].upper()] = l['id']
        return speed_dict

    @api.model
    def _match_account(self, account_dict, chatter_msg, speed_dict=None):
        """Example:
        account_dict = {
            'code': '411100',
            }
        speed_dict is usefull to gain performance when you have a lot of
        accounts to match
        """
        if not account_dict:
            account_dict = {}
        aao = self.env['account.account']
        if speed_dict is None:
            speed_dict = self._prepare_account_speed_dict()
        self._strip_cleanup_dict(account_dict)
        if account_dict.get('recordset'):
            return account_dict['recordset']
        if account_dict.get('id'):
            return aao.browse(account_dict['id'])
        if account_dict.get('code'):
            acc_code = account_dict['code'].upper()
            if acc_code in speed_dict:
                return aao.browse(speed_dict[acc_code])
            # Match when account_dict['code'] is longer than Odoo's account
            # codes because of trailing '0'
            # I don't think we need a warning for this kind of match
            acc_code_tmp = acc_code
            while acc_code_tmp and acc_code_tmp[-1] == '0':
                acc_code_tmp = acc_code_tmp[:-1]
                if acc_code_tmp and acc_code_tmp in speed_dict:
                    return aao.browse(speed_dict[acc_code_tmp])
            # Match when account_dict['code'] is shorter than Odoo's accounts
            # -> warns the user about this
            for code, account_id in speed_dict.items():
                if code.startswith(acc_code):
                    chatter_msg.append(_(
                        "Approximate match: account %s has been matched "
                        "with account %s") % (account_dict['code'], code))
                    return aao.browse(account_id)
        raise self.user_error_wrap(_(
            "Odoo couldn't find any account corresponding to the "
            "following information extracted from the business document: "
            "Account code: %s") % account_dict.get('code'))

    def _prepare_analytic_account_speed_dict(self):
        res = self.env['account.analytic.account'].search_read(
            [('company_id', '=', self.env.user.company_id.id)],
            ['code'])
        speed_dict = {}
        for l in res:
            if l['code']:
                speed_dict[l['code'].upper()] = l['id']
        return speed_dict

    @api.model
    def _match_analytic_account(
            self, aaccount_dict, chatter_msg, speed_dict=None):
        """Example:
        aaccount_dict = {
            'code': '627',
            }
        speed_dict is usefull to gain performance when you have a lot of
        analytic accounts to match
        """
        if not aaccount_dict:
            aaccount_dict = {}
        aaao = self.env['account.analytic.account']
        if speed_dict is None:
            speed_dict = self._prepare_analytic_account_speed_dict()
        self._strip_cleanup_dict(aaccount_dict)
        if aaccount_dict.get('recordset'):
            return aaccount_dict['recordset']
        if aaccount_dict.get('id'):
            return aaao.browse(aaccount_dict['id'])
        if aaccount_dict.get('code'):
            aacode = aaccount_dict['code'].upper()
            if aacode in speed_dict:
                return aaao.browse(speed_dict[aacode])
        raise self.user_error_wrap(_(
            "Odoo couldn't find any analytic account corresponding to the "
            "following information extracted from the business document: "
            "Analytic account code: %s") % aaccount_dict.get('code'))

    def _prepare_journal_speed_dict(self):
        res = self.env['account.journal'].search_read([
            ('company_id', '=', self.env.user.company_id.id)], ['code'])
        speed_dict = {}
        for l in res:
            speed_dict[l['code'].upper()] = l['id']
        return speed_dict

    @api.model
    def _match_journal(self, journal_dict, chatter_msg, speed_dict=None):
        """Example:
        journal_dict = {
            'code': 'MISC',
            }
        speed_dict is usefull to gain performance when you have a lot of
        journals to match
        """
        if not journal_dict:
            journal_dict = {}
        ajo = self.env['account.account']
        if speed_dict is None:
            speed_dict = self._prepare_journal_speed_dict()
        self._strip_cleanup_dict(journal_dict)
        if journal_dict.get('recordset'):
            return journal_dict['recordset']
        if journal_dict.get('id'):
            return ajo.browse(journal_dict['id'])
        if journal_dict.get('code'):
            jcode = journal_dict['code'].upper()
            if jcode in speed_dict:
                return ajo.browse(speed_dict[jcode])
            # case insensitive
        raise self.user_error_wrap(_(
            "Odoo couldn't find any journal corresponding to the "
            "following information extracted from the business document: "
            "Journal code: %s") % journal_dict.get('code'))

    def get_xml_files_from_pdf(self, pdf_file):
        """Returns a dict with key = filename, value = XML file obj"""
        logger.info('Trying to find an embedded XML file inside PDF')
        res = {}
        try:
            fd = BytesIO(pdf_file)
            pdf = PyPDF2.PdfFileReader(fd)
            logger.debug('pdf.trailer=%s', pdf.trailer)
            pdf_root = pdf.trailer['/Root']
            logger.debug('pdf_root=%s', pdf_root)
            embeddedfiles = pdf_root['/Names']['/EmbeddedFiles']['/Names']
            i = 0
            xmlfiles = {}  # key = filename, value = PDF obj
            for embeddedfile in embeddedfiles[:-1]:
                mime_res = mimetypes.guess_type(embeddedfile)
                if mime_res and mime_res[0] in ['application/xml', 'text/xml']:
                    xmlfiles[embeddedfile] = embeddedfiles[i + 1]
                i += 1
            logger.debug('xmlfiles=%s', xmlfiles)
            for filename, xml_file_dict_obj in xmlfiles.items():
                try:
                    xml_file_dict = xml_file_dict_obj.getObject()
                    logger.debug('xml_file_dict=%s', xml_file_dict)
                    xml_string = xml_file_dict['/EF']['/F'].getData()
                    xml_root = etree.fromstring(xml_string)
                    logger.debug(
                        'A valid XML file %s has been found in the PDF file',
                        filename)
                    res[filename] = xml_root
                except Exception as e:
                    continue
        except Exception as e:
            pass
        logger.info('Valid XML files found in PDF: %s', list(res.keys()))
        return res

    @api.model
    def post_create_or_update(self, parsed_dict, record, doc_filename=None):
        if parsed_dict.get('attachments'):
            for filename, data_base64 in\
                    parsed_dict['attachments'].items():
                self.env['ir.attachment'].create({
                    'name': filename,
                    'res_id': record.id,
                    'res_model': str(record._name),
                    'datas': data_base64,
                    'datas_fname': filename,
                })
        for msg in parsed_dict['chatter_msg']:
            record.message_post(msg)
        if parsed_dict.get('note'):
            if doc_filename:
                msg = _('<b>Notes in file %s:</b>') % doc_filename
            else:
                msg = _('<b>Notes in imported document:</b>')
            record.message_post(  # pylint: disable=translation-required
                '%s %s' % (msg, parsed_dict['note']))
