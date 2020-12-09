# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EDIInputProcessBusinessDocumentImport(AbstractComponent):
    _name = "edi.input.process.business.document.import"
    _inherit = "edi.component.input.mixin"

    def process(self):
        raise NotImplementedError()

    def _user_error_wrap(self, error_msg):
        return self.env["business.document.import"].user_error_wrap(error_msg)

    def _strip_cleanup_dict(self, match_dict):
        return self.env["business.document.import"]._strip_cleanup_dict(match_dict)

    def _match_partner_contact(self, partner_dict, domain, order):
        return self.env["business.document.import"]._match_partner_contact(
            partner_dict, domain, order
        )

    def _match_partner(
        self,
        partner_dict,
        chatter_msg,
        partner_type="supplier",
        domain=None,
        raise_exception=True,
    ):
        return self.env["business.document.import"]._match_partner(
            partner_dict,
            chatter_msg,
            partner_type=partner_type,
            domain=domain,
            raise_exception=raise_exception,
        )

    def _hook_match_partner(
        self, partner_dict, chatter_msg, domain, partner_type_label
    ):
        return self.env["business.document.import"]._hook_match_partner(
            partner_dict, chatter_msg, domain, partner_type_label
        )

    def _match_shipping_partner(
        self, partner_dict, partner, chatter_msg, domain=None, raise_exception=True
    ):
        return self.env["business.document.import"]._match_shipping_partner(
            partner_dict,
            partner,
            chatter_msg,
            domain=domain,
            raise_exception=raise_exception,
        )

    def _match_partner_bank(
        self, partner, iban, bic, chatter_msg, create_if_not_found=False
    ):

        return self.env["business.document.import"]._match_partner_bank(
            partner, iban, bic, chatter_msg, create_if_not_found=create_if_not_found
        )

    def _match_product(self, product_dict, chatter_msg, seller=False):
        return self.env["business.document.import"]._match_product(
            product_dict, chatter_msg, seller=seller
        )

    def _match_currency(self, currency_dict, chatter_msg):
        return self.env["business.document.import"]._match_currency(
            currency_dict, chatter_msg
        )

    def _match_uom(self, uom_dict, chatter_msg, product=False):
        return self.env["business.document.import"]._match_uom(
            uom_dict, chatter_msg, product=product
        )

    def _match_taxes(
        self, taxes_list, chatter_msg, type_tax_use="purchase", price_include=False
    ):
        return self.env["business.document.import"]._match_taxes(
            taxes_list,
            chatter_msg,
            type_tax_use=type_tax_use,
            price_include=price_include,
        )

    def _match_tax(
        self, tax_dict, chatter_msg, type_tax_use="purchase", price_include=False
    ):
        return self.env["business.document.import"]._match_tax(
            tax_dict,
            chatter_msg,
            type_tax_use=type_tax_use,
            price_include=price_include,
        )

    def _compare_lines(
        self,
        existing_lines,
        import_lines,
        chatter_msg,
        qty_precision=None,
        price_precision=None,
        seller=False,
    ):
        return self.env["business.document.import"].compare_lines(
            existing_lines,
            import_lines,
            chatter_msg,
            qty_precision=qty_precision,
            price_precision=price_precision,
            seller=seller,
        )

    def _prepare_account_speed_dict(self):
        return self.env["business.document.import"]._prepare_account_speed_dict()

    def _match_account(self, account_dict, chatter_msg, speed_dict=None):
        return self.env["business.document.import"]._match_account(
            account_dict, chatter_msg, speed_dict=speed_dict
        )

    def _prepare_analytic_account_speed_dict(self):
        return self.env[
            "business.document.import"
        ]._prepare_analytic_account_speed_dict()

    def _match_analytic_account(self, aaccount_dict, chatter_msg, speed_dict=None):
        return self.env["business.document.import"]._match_analytic_account(
            aaccount_dict, chatter_msg, speed_dict=speed_dict
        )

    def _prepare_journal_speed_dict(self):
        return self.env["business.document.import"]._prepare_journal_speed_dict()

    def _match_journal(self, journal_dict, chatter_msg, speed_dict=None):
        return self.env["business.document.import"]._match_journal(
            journal_dict, chatter_msg, speed_dict=speed_dict
        )

    def _match_incoterm(self, incoterm_dict, chatter_msg):
        return self.env["business.document.import"]._match_incoterm(
            incoterm_dict, chatter_msg
        )

    def _check_company(self, company_dict, chatter_msg):
        return self.env["business.document.import"]._check_company(
            company_dict, chatter_msg
        )

    def _get_xml_files_from_pdf(self, pdf_file):
        return self.env["business.document.import"].get_xml_files_from_pdf(pdf_file)

    def _post_create_or_update(self, parsed_dict, record, doc_filename=None):
        return self.env["business.document.import"].post_create_or_update(
            parsed_dict, record, doc_filename=doc_filename
        )
