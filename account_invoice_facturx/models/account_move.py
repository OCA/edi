# Copyright 2016-2020 Akretion France (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round

logger = logging.getLogger(__name__)

try:
    from facturx import generate_facturx_from_binary, check_facturx_xsd
except ImportError:
    logger.debug("Cannot import facturx")


FACTURX_FILENAME = "factur-x.xml"
DIRECT_DEBIT_CODES = ("49", "59")
CREDIT_TRF_CODES = ("30", "31", "42")
PROFILES_EN_UP = ["en16931", "extended"]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "base.facturx"]

    @api.model
    def _cii_add_address_block(self, partner, parent_node, ns):
        address = etree.SubElement(parent_node, ns["ram"] + "PostalTradeAddress")
        if ns["level"] != "minimum":
            if partner.zip:
                address_zip = etree.SubElement(address, ns["ram"] + "PostcodeCode")
                address_zip.text = partner.zip
            if partner.street:
                address_street = etree.SubElement(address, ns["ram"] + "LineOne")
                address_street.text = partner.street
                if partner.street2:
                    address_street2 = etree.SubElement(address, ns["ram"] + "LineTwo")
                    address_street2.text = partner.street2
            if partner.city:
                address_city = etree.SubElement(address, ns["ram"] + "CityName")
                address_city.text = partner.city
        if not partner.country_id:
            raise UserError(
                _(
                    "Country is not set on partner '%s'. In the Factur-X "
                    "standard, the country is required for buyer and seller."
                    % partner.display_name
                )
            )
        address_country = etree.SubElement(address, ns["ram"] + "CountryID")
        address_country.text = partner.country_id.code

    @api.model
    def _cii_trade_contact_department_name(self, partner):
        return None

    @api.model
    def _cii_add_trade_contact_block(self, partner, parent_node, ns):
        trade_contact = etree.SubElement(parent_node, ns["ram"] + "DefinedTradeContact")
        contact_name = etree.SubElement(trade_contact, ns["ram"] + "PersonName")
        contact_name.text = partner.name
        department = self._cii_trade_contact_department_name(partner)
        if department:
            department_name = etree.SubElement(
                trade_contact, ns["ram"] + "DepartmentName"
            )
            department_name.text = department
        phone = partner.phone or partner.mobile
        if phone:
            phone_node = etree.SubElement(
                trade_contact, ns["ram"] + "TelephoneUniversalCommunication"
            )
            phone_number = etree.SubElement(phone_node, ns["ram"] + "CompleteNumber")
            phone_number.text = phone
        if partner.email:
            email_node = etree.SubElement(
                trade_contact, ns["ram"] + "EmailURIUniversalCommunication"
            )
            email_uriid = etree.SubElement(
                email_node, ns["ram"] + "URIID", schemeID="SMTP"
            )
            email_uriid.text = partner.email

    @api.model
    def _cii_add_date(
        self, node_name, date_datetime, parent_node, ns, date_ns_type="udt"
    ):
        date_node = etree.SubElement(parent_node, ns["ram"] + node_name)
        date_node_str = etree.SubElement(
            date_node, ns[date_ns_type] + "DateTimeString", format="102"
        )
        # 102 = format YYYYMMDD
        date_node_str.text = date_datetime.strftime("%Y%m%d")

    def _cii_add_document_context_block(self, root, nsmap, ns):
        self.ensure_one()
        doc_ctx = etree.SubElement(root, ns["rsm"] + "ExchangedDocumentContext")
        # TestIndicator not in factur-X...
        # if self.state not in ('open', 'paid'):
        #    test_indic = etree.SubElement(
        #        doc_ctx, ns['ram'] + 'TestIndicator')
        #    indic = etree.SubElement(test_indic, ns['udt'] + 'Indicator')
        #    indic.text = 'true'
        ctx_param = etree.SubElement(
            doc_ctx, ns["ram"] + "GuidelineSpecifiedDocumentContextParameter"
        )
        ctx_param_id = etree.SubElement(ctx_param, ns["ram"] + "ID")
        if ns["level"] == "en16931":
            urn = "urn:cen.eu:en16931:2017"
        elif ns["level"] == "basic":
            urn = "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic"
        elif ns["level"] == "extended":
            urn = "urn:cen.eu:en16931:2017#conformant#" "urn:factur-x.eu:1p0:extended"
        else:
            urn = "urn:factur-x.eu:1p0:%s" % ns["level"]
        ctx_param_id.text = urn

    def _cii_add_header_block(self, root, ns):
        self.ensure_one()
        header_doc = etree.SubElement(root, ns["rsm"] + "ExchangedDocument")
        header_doc_id = etree.SubElement(header_doc, ns["ram"] + "ID")
        if self.state == "posted":
            header_doc_id.text = self.name
        else:
            header_doc_id.text = self.state
        header_doc_typecode = etree.SubElement(header_doc, ns["ram"] + "TypeCode")
        if self.type == "out_invoice":
            header_doc_typecode.text = "380"
        elif self.type == "out_refund":
            header_doc_typecode.text = ns["refund_type"]
        # 2 options allowed in Factur-X :
        # a) invoice and refunds -> 380 ; negative amounts if refunds
        # b) invoice -> 380 refunds -> 381, with positive amounts
        # In ZUGFeRD samples, they use option a)
        # For Chorus, they impose option b)
        # Until August 2017, I was using option a), now I use option b)
        # Starting from November 2017, it's a config option !
        invoice_date_dt = self.invoice_date or fields.Date.context_today(self)
        self._cii_add_date("IssueDateTime", invoice_date_dt, header_doc, ns)
        if self.narration and ns["level"] != "minimum":
            note = etree.SubElement(header_doc, ns["ram"] + "IncludedNote")
            content_note = etree.SubElement(note, ns["ram"] + "Content")
            content_note.text = self.narration

    @api.model
    def _cii_get_party_identification(self, commercial_partner):
        """This method is designed to be inherited in localisation modules
        Should return a dict with key=SchemeName, value=Identifier"""
        return {}

    @api.model
    def _cii_add_party_identification(self, commercial_partner, parent_node, ns):
        id_dict = self._cii_get_party_identification(commercial_partner)
        if id_dict:
            party_identification = etree.SubElement(
                parent_node, ns["ram"] + "SpecifiedLegalOrganization"
            )
            for scheme_name, party_id_text in id_dict.items():
                party_identification_id = etree.SubElement(
                    party_identification, ns["ram"] + "ID", schemeID=scheme_name
                )
                party_identification_id.text = party_id_text
        return

    @api.model
    def _cii_trade_agreement_buyer_ref(self, partner):
        return None

    def _cii_add_trade_agreement_block(self, trade_transaction, ns):
        self.ensure_one()
        company = self.company_id
        trade_agreement = etree.SubElement(
            trade_transaction, ns["ram"] + "ApplicableHeaderTradeAgreement"
        )
        buyer_ref = self._cii_trade_agreement_buyer_ref(self.partner_id)
        if buyer_ref:
            buyer_reference = etree.SubElement(
                trade_agreement, ns["ram"] + "BuyerReference"
            )
            buyer_reference.text = buyer_ref
        seller = etree.SubElement(trade_agreement, ns["ram"] + "SellerTradeParty")
        seller_name = etree.SubElement(seller, ns["ram"] + "Name")
        seller_name.text = company.name
        self._cii_add_party_identification(company.partner_id, seller, ns)
        if ns["level"] in PROFILES_EN_UP:
            self._cii_add_trade_contact_block(
                self.invoice_user_id.partner_id or company.partner_id, seller, ns
            )
        self._cii_add_address_block(company.partner_id, seller, ns)
        if company.vat:
            seller_tax_reg = etree.SubElement(
                seller, ns["ram"] + "SpecifiedTaxRegistration"
            )
            seller_tax_reg_id = etree.SubElement(
                seller_tax_reg, ns["ram"] + "ID", schemeID="VA"
            )
            seller_tax_reg_id.text = company.vat
        buyer = etree.SubElement(trade_agreement, ns["ram"] + "BuyerTradeParty")
        if ns["level"] != "minimum" and self.commercial_partner_id.ref:
            buyer_id = etree.SubElement(buyer, ns["ram"] + "ID")
            buyer_id.text = self.commercial_partner_id.ref
        buyer_name = etree.SubElement(buyer, ns["ram"] + "Name")
        buyer_name.text = self.commercial_partner_id.name
        self._cii_add_party_identification(self.commercial_partner_id, buyer, ns)
        if (
            ns["level"] in PROFILES_EN_UP
            and self.commercial_partner_id != self.partner_id
            and self.partner_id.name
        ):
            self._cii_add_trade_contact_block(self.partner_id, buyer, ns)
        self._cii_add_address_block(self.partner_id, buyer, ns)
        if self.commercial_partner_id.vat:
            buyer_tax_reg = etree.SubElement(
                buyer, ns["ram"] + "SpecifiedTaxRegistration"
            )
            buyer_tax_reg_id = etree.SubElement(
                buyer_tax_reg, ns["ram"] + "ID", schemeID="VA"
            )
            buyer_tax_reg_id.text = self.commercial_partner_id.vat
        self._cii_add_buyer_order_reference(trade_agreement, ns)
        self._cii_add_contract_reference(trade_agreement, ns)

    def _cii_add_buyer_order_reference(self, trade_agreement, ns):
        self.ensure_one()
        if self.ref:
            buyer_order_ref = etree.SubElement(
                trade_agreement, ns["ram"] + "BuyerOrderReferencedDocument"
            )
            buyer_order_id = etree.SubElement(
                buyer_order_ref, ns["ram"] + "IssuerAssignedID"
            )
            buyer_order_id.text = self.ref

    def _cii_add_contract_reference(self, trade_agreement, ns):
        self.ensure_one()
        # agreement_id is provided by the OCA module agreement_account
        if (
            ns["level"] != "minimum"
            and hasattr(self, "agreement_id")
            and self.agreement_id
            and self.agreement_id.code
        ):
            contract_ref = etree.SubElement(
                trade_agreement, ns["ram"] + "ContractReferencedDocument"
            )
            contract_id = etree.SubElement(contract_ref, ns["ram"] + "IssuerAssignedID")
            contract_id.text = self.agreement_id.code

    def _cii_add_trade_delivery_block(self, trade_transaction, ns):
        self.ensure_one()
        trade_agreement = etree.SubElement(
            trade_transaction, ns["ram"] + "ApplicableHeaderTradeDelivery"
        )
        # partner_shipping_id is provided by the sale module
        if (
            ns["level"] in PROFILES_EN_UP
            and hasattr(self, "partner_shipping_id")
            and self.partner_shipping_id
        ):
            shipto_trade_party = etree.SubElement(
                trade_agreement, ns["ram"] + "ShipToTradeParty"
            )
            self._cii_add_address_block(
                self.partner_shipping_id, shipto_trade_party, ns
            )
        return trade_agreement

    def _cii_add_trade_settlement_payment_means_block(self, trade_settlement, ns):
        payment_means = etree.SubElement(
            trade_settlement, ns["ram"] + "SpecifiedTradeSettlementPaymentMeans"
        )
        payment_means_code = etree.SubElement(payment_means, ns["ram"] + "TypeCode")
        if ns["level"] in PROFILES_EN_UP:
            payment_means_info = etree.SubElement(
                payment_means, ns["ram"] + "Information"
            )
        if self.payment_mode_id:
            payment_means_code.text = self.payment_mode_id.payment_method_id.unece_code
            if ns["level"] in PROFILES_EN_UP:
                payment_means_info.text = (
                    self.payment_mode_id.note or self.payment_mode_id.name
                )
        else:
            payment_means_code.text = "30"  # use 30 and not 31,
            # for wire transfer, according to Factur-X CIUS
            if ns["level"] in PROFILES_EN_UP:
                payment_means_info.text = _("Wire transfer")
            logger.warning(
                "Missing payment mode on invoice ID %d. "
                "Using 30 (wire transfer) as UNECE code as fallback "
                "for payment mean",
                self.id,
            )
        if payment_means_code.text in CREDIT_TRF_CODES:
            partner_bank = self.invoice_partner_bank_id
            if (
                not partner_bank
                and self.payment_mode_id
                and self.payment_mode_id.bank_account_link == "fixed"
                and self.payment_mode_id.fixed_journal_id
            ):
                partner_bank = self.payment_mode_id.fixed_journal_id.bank_account_id
            if partner_bank and partner_bank.acc_type == "iban":
                payment_means_bank_account = etree.SubElement(
                    payment_means, ns["ram"] + "PayeePartyCreditorFinancialAccount"
                )
                iban = etree.SubElement(
                    payment_means_bank_account, ns["ram"] + "IBANID"
                )
                iban.text = partner_bank.sanitized_acc_number
                if ns["level"] in PROFILES_EN_UP and partner_bank.bank_bic:
                    payment_means_bank = etree.SubElement(
                        payment_means,
                        ns["ram"] + "PayeeSpecifiedCreditorFinancialInstitution",
                    )
                    payment_means_bic = etree.SubElement(
                        payment_means_bank, ns["ram"] + "BICID"
                    )
                    payment_means_bic.text = partner_bank.bank_bic
        # Field mandate_id provided by the OCA module account_banking_mandate
        elif (
            payment_means_code.text in DIRECT_DEBIT_CODES
            and hasattr(self, "mandate_id")
            and self.mandate_id.partner_bank_id
            and self.mandate_id.partner_bank_id.acc_type == "iban"
            and self.mandate_id.partner_bank_id.sanitized_acc_number
        ):
            debtor_acc = etree.SubElement(
                payment_means, ns["ram"] + "PayerPartyDebtorFinancialAccount"
            )
            debtor_acc_iban = etree.SubElement(debtor_acc, ns["ram"] + "IBANID")
            debtor_acc_iban.text = self.mandate_id.partner_bank_id.sanitized_acc_number

    def _cii_trade_payment_terms_block(self, trade_settlement, ns):
        trade_payment_term = etree.SubElement(
            trade_settlement, ns["ram"] + "SpecifiedTradePaymentTerms"
        )
        if ns["level"] in PROFILES_EN_UP:
            trade_payment_term_desc = etree.SubElement(
                trade_payment_term, ns["ram"] + "Description"
            )
            # The 'Description' field of SpecifiedTradePaymentTerms
            # is a required field, so we must always give a value
            if self.invoice_payment_term_id:
                trade_payment_term_desc.text = self.invoice_payment_term_id.name
            else:
                trade_payment_term_desc.text = _("No specific payment term selected")

        if self.invoice_date_due:
            self._cii_add_date(
                "DueDateDateTime", self.invoice_date_due, trade_payment_term, ns
            )

        # Direct debit Mandate
        if (
            self.payment_mode_id.payment_method_id.unece_code in DIRECT_DEBIT_CODES
            and hasattr(self, "mandate_id")
            and self.mandate_id.unique_mandate_reference
        ):
            mandate = etree.SubElement(
                trade_payment_term, ns["ram"] + "DirectDebitMandateID"
            )
            mandate.text = self.mandate_id.unique_mandate_reference

    def _cii_applicable_trade_tax_block(
        self, tax, tax_amount, base_amount, trade_settlement, ns
    ):
        if ns["level"] == "minimum":
            return
        if not tax.unece_type_code:
            raise UserError(_("Missing UNECE Tax Type on tax '%s'") % tax.display_name)
        if not tax.unece_categ_code:
            raise UserError(
                _("Missing UNECE Tax Category on tax '%s'") % tax.display_name
            )
        trade_tax = etree.SubElement(trade_settlement, ns["ram"] + "ApplicableTradeTax")
        amount = etree.SubElement(trade_tax, ns["ram"] + "CalculatedAmount")
        amount.text = "%0.*f" % (ns["cur_prec"], tax_amount * ns["sign"])
        tax_type = etree.SubElement(trade_tax, ns["ram"] + "TypeCode")
        tax_type.text = tax.unece_type_code

        if (
            tax.unece_categ_code != "S"
            and float_is_zero(tax_amount, precision_digits=ns["cur_prec"])
            and self.fiscal_position_id
            and self.fiscal_position_id.note
        ):
            exemption_reason = etree.SubElement(
                trade_tax, ns["ram"] + "ExemptionReason"
            )
            exemption_reason.text = self.with_context(
                lang=self.partner_id.lang or "en_US"
            ).fiscal_position_id.note

        base = etree.SubElement(trade_tax, ns["ram"] + "BasisAmount")
        base.text = "%0.*f" % (ns["cur_prec"], base_amount * ns["sign"])
        tax_categ_code = etree.SubElement(trade_tax, ns["ram"] + "CategoryCode")
        tax_categ_code.text = tax.unece_categ_code
        if tax.unece_due_date_code:
            trade_tax_due_date = etree.SubElement(
                trade_tax, ns["ram"] + "DueDateTypeCode"
            )
            trade_tax_due_date.text = tax.unece_due_date_code
            # This field is not required, so no error if missing
        if tax.amount_type == "percent":
            percent = etree.SubElement(trade_tax, ns["ram"] + "RateApplicablePercent")
            percent.text = "%0.*f" % (2, tax.amount)

    def _cii_add_trade_settlement_block(self, trade_transaction, ns):
        self.ensure_one()
        trade_settlement = etree.SubElement(
            trade_transaction, ns["ram"] + "ApplicableHeaderTradeSettlement"
        )
        # ICS, provided by the OCA module account_banking_sepa_direct_debit
        if (
            ns["level"] != "minimum"
            and self.payment_mode_id.payment_method_id.unece_code in DIRECT_DEBIT_CODES
            and hasattr(self.company_id, "sepa_creditor_identifier")
            and self.company_id.sepa_creditor_identifier
        ):
            ics = etree.SubElement(trade_settlement, ns["ram"] + "CreditorReferenceID")
            ics.text = self.company_id.sepa_creditor_identifier

        if ns["level"] != "minimum":
            payment_ref = etree.SubElement(
                trade_settlement, ns["ram"] + "PaymentReference"
            )
            payment_ref.text = self.name or self.state
        invoice_currency = etree.SubElement(
            trade_settlement, ns["ram"] + "InvoiceCurrencyCode"
        )
        invoice_currency.text = ns["currency"]
        if (
            self.payment_mode_id
            and not self.payment_mode_id.payment_method_id.unece_code
        ):
            raise UserError(
                _("Missing UNECE code on payment method '%s'")
                % self.payment_mode_id.payment_method_id.display_name
            )
        if ns["level"] != "minimum" and not (
            self.type == "out_refund"
            and self.payment_mode_id
            and self.payment_mode_id.payment_method_id.unece_code in CREDIT_TRF_CODES
        ):
            self._cii_add_trade_settlement_payment_means_block(trade_settlement, ns)

        tax_basis_total = 0.0
        for tline in self.line_ids.filtered(lambda x: x.tax_line_id):
            tax_base_amount = tline.tax_base_amount
            self._cii_applicable_trade_tax_block(
                tline.tax_line_id,
                tline.price_subtotal,
                tax_base_amount,
                trade_settlement,
                ns,
            )
            tax_basis_total += tax_base_amount
        tax_zero_amount = {}  # key = tax recordset, value = base
        for line in self.line_ids:
            for tax in line.tax_ids.filtered(
                lambda t: float_is_zero(t.amount, precision_digits=ns["cur_prec"])
            ):
                tax_zero_amount.setdefault(tax, 0.0)
                tax_zero_amount[tax] += line.price_subtotal
        for tax, tax_base_amount in tax_zero_amount.items():
            self._cii_applicable_trade_tax_block(
                tax, 0, tax_base_amount, trade_settlement, ns
            )
            tax_basis_total += tax_base_amount

        if ns["level"] != "minimum":
            self._cii_trade_payment_terms_block(trade_settlement, ns)

        self._cii_monetary_summation_block(trade_settlement, tax_basis_total, ns)
        # TODO find remplacement of field refund_invoice_id
        # if self.refund_invoice_id and self.refund_invoice_id.number:
        #    inv_ref_doc = etree.SubElement(
        #        trade_settlement, ns['ram'] + 'InvoiceReferencedDocument')
        #    inv_ref_doc_num = etree.SubElement(
        #        inv_ref_doc, ns['ram'] + 'IssuerAssignedID')
        #    inv_ref_doc_num.text = self.refund_invoice_id.number
        #    self._cii_add_date(
        #        'FormattedIssueDateTime', self.refund_invoice_id.invoice_date,
        #        inv_ref_doc, ns, date_ns_type='qdt')

    def _cii_monetary_summation_block(self, trade_settlement, tax_basis_total, ns):
        sums = etree.SubElement(
            trade_settlement,
            ns["ram"] + "SpecifiedTradeSettlementHeaderMonetarySummation",
        )
        if ns["level"] != "minimum":
            line_total = etree.SubElement(sums, ns["ram"] + "LineTotalAmount")
            line_total.text = "%0.*f" % (
                ns["cur_prec"],
                self.amount_untaxed * ns["sign"],
            )
        # In Factur-X, charge total amount and allowance total are not required
        # charge_total = etree.SubElement(
        #    sums, ns['ram'] + 'ChargeTotalAmount')
        # charge_total.text = '0.00'
        # allowance_total = etree.SubElement(
        #    sums, ns['ram'] + 'AllowanceTotalAmount')
        # allowance_total.text = '0.00'
        tax_basis_total_amt = etree.SubElement(sums, ns["ram"] + "TaxBasisTotalAmount")
        tax_basis_total_amt.text = "%0.*f" % (
            ns["cur_prec"],
            tax_basis_total * ns["sign"],
        )
        tax_total = etree.SubElement(
            sums, ns["ram"] + "TaxTotalAmount", currencyID=ns["currency"]
        )
        tax_total.text = "%0.*f" % (ns["cur_prec"], self.amount_tax * ns["sign"])
        total = etree.SubElement(sums, ns["ram"] + "GrandTotalAmount")
        total.text = "%0.*f" % (ns["cur_prec"], self.amount_total * ns["sign"])
        if ns["level"] != "minimum":
            prepaid = etree.SubElement(sums, ns["ram"] + "TotalPrepaidAmount")
            prepaid.text = "%0.*f" % (
                ns["cur_prec"],
                (self.amount_total - self.amount_residual) * ns["sign"],
            )
        residual = etree.SubElement(sums, ns["ram"] + "DuePayableAmount")
        residual.text = "%0.*f" % (ns["cur_prec"], self.amount_residual * ns["sign"])

    def _set_iline_product_name(self, iline, trade_product, ns):
        if iline.product_id:
            if iline.product_id.barcode:
                barcode = etree.SubElement(
                    trade_product, ns["ram"] + "GlobalID", schemeID="0160"
                )
                # 0160 = GS1 Global Trade Item Number (GTIN, EAN)
                barcode.text = iline.product_id.barcode
            if ns["level"] in PROFILES_EN_UP and iline.product_id.default_code:
                product_code = etree.SubElement(
                    trade_product, ns["ram"] + "SellerAssignedID"
                )
                product_code.text = iline.product_id.default_code
        product_name = etree.SubElement(trade_product, ns["ram"] + "Name")
        product_name.text = iline.name

    def _cii_add_invoice_line_block(self, trade_transaction, iline, line_number, ns):
        self.ensure_one()
        line_item = etree.SubElement(
            trade_transaction, ns["ram"] + "IncludedSupplyChainTradeLineItem"
        )
        line_doc = etree.SubElement(
            line_item, ns["ram"] + "AssociatedDocumentLineDocument"
        )
        etree.SubElement(line_doc, ns["ram"] + "LineID").text = str(line_number)

        trade_product = etree.SubElement(line_item, ns["ram"] + "SpecifiedTradeProduct")
        self._set_iline_product_name(iline, trade_product, ns)
        if (
            ns["level"] in PROFILES_EN_UP
            and iline.product_id
            and iline.product_id.description_sale
        ):
            product_desc = etree.SubElement(trade_product, ns["ram"] + "Description")
            product_desc.text = iline.product_id.description_sale

        line_trade_agreement = etree.SubElement(
            line_item, ns["ram"] + "SpecifiedLineTradeAgreement"
        )
        if float_compare(iline.price_unit, 0, precision_digits=ns["price_prec"]) < 0:
            raise UserError(
                _(
                    "The Factur-X standard specify that unit prices can't be "
                    "negative. The unit price of line '%s' is negative. You "
                    "should generate a customer refund for that line."
                )
                % iline.name
            )
        # convert gross price_unit to tax_excluded value
        taxres = iline.tax_ids.compute_all(iline.price_unit)
        gross_price_val = float_round(
            taxres["total_excluded"], precision_digits=ns["price_prec"]
        )
        # Use oline.price_subtotal/qty to compute net unit price to be sure
        # to get a *tax_excluded* net unit price
        if float_is_zero(iline.quantity, precision_digits=ns["qty_prec"]):
            net_price_val = 0.0
        else:
            net_price_val = float_round(
                iline.price_subtotal / float(iline.quantity),
                precision_digits=ns["price_prec"],
            )
        if ns["level"] in PROFILES_EN_UP:
            gross_price = etree.SubElement(
                line_trade_agreement, ns["ram"] + "GrossPriceProductTradePrice"
            )
            gross_price_amount = etree.SubElement(
                gross_price, ns["ram"] + "ChargeAmount"
            )
            gross_price_amount.text = "%0.*f" % (ns["price_prec"], gross_price_val)
            fc_discount = float_compare(
                iline.discount, 0.0, precision_digits=ns["disc_prec"]
            )
            if fc_discount in [-1, 1]:
                trade_allowance = etree.SubElement(
                    gross_price, ns["ram"] + "AppliedTradeAllowanceCharge"
                )
                charge_indic = etree.SubElement(
                    trade_allowance, ns["ram"] + "ChargeIndicator"
                )
                indicator = etree.SubElement(charge_indic, ns["udt"] + "Indicator")
                if fc_discount == 1:
                    indicator.text = "false"
                else:
                    indicator.text = "true"
                actual_amount = etree.SubElement(
                    trade_allowance, ns["ram"] + "ActualAmount"
                )
                actual_amount_val = float_round(
                    gross_price_val - net_price_val, precision_digits=ns["price_prec"]
                )
                actual_amount.text = "%0.*f" % (
                    ns["price_prec"],
                    actual_amount_val * ns["sign"],
                )

        net_price = etree.SubElement(
            line_trade_agreement, ns["ram"] + "NetPriceProductTradePrice"
        )
        net_price_amount = etree.SubElement(net_price, ns["ram"] + "ChargeAmount")
        net_price_amount.text = "%0.*f" % (ns["price_prec"], net_price_val)
        line_trade_delivery = etree.SubElement(
            line_item, ns["ram"] + "SpecifiedLineTradeDelivery"
        )
        if iline.product_uom_id and iline.product_uom_id.unece_code:
            unitCode = iline.product_uom_id.unece_code
        else:
            unitCode = "C62"
            if not iline.product_uom_id:
                logger.warning(
                    "No unit of measure on invoice line '%s', "
                    "using C62 (piece) as fallback",
                    iline.name,
                )
            else:
                logger.warning(
                    "Missing UNECE Code on unit of measure %s, "
                    "using C62 (piece) as fallback",
                    iline.product_uom_id.name,
                )
        billed_qty = etree.SubElement(
            line_trade_delivery, ns["ram"] + "BilledQuantity", unitCode=unitCode
        )
        billed_qty.text = "%0.*f" % (ns["qty_prec"], iline.quantity * ns["sign"])
        line_trade_settlement = etree.SubElement(
            line_item, ns["ram"] + "SpecifiedLineTradeSettlement"
        )

        if iline.tax_ids:
            for tax in iline.tax_ids:
                trade_tax = etree.SubElement(
                    line_trade_settlement, ns["ram"] + "ApplicableTradeTax"
                )
                trade_tax_typecode = etree.SubElement(trade_tax, ns["ram"] + "TypeCode")
                if not tax.unece_type_code:
                    raise UserError(
                        _("Missing UNECE Tax Type on tax '%s'") % tax.display_name
                    )
                trade_tax_typecode.text = tax.unece_type_code
                trade_tax_categcode = etree.SubElement(
                    trade_tax, ns["ram"] + "CategoryCode"
                )
                if not tax.unece_categ_code:
                    raise UserError(
                        _("Missing UNECE Tax Category on tax '%s'") % tax.display_name
                    )
                trade_tax_categcode.text = tax.unece_categ_code
                # No 'DueDateTypeCode' on lines
                if tax.amount_type == "percent":
                    trade_tax_percent = etree.SubElement(
                        trade_tax, ns["ram"] + "RateApplicablePercent"
                    )
                    trade_tax_percent.text = "%0.*f" % (2, tax.amount)
        # Fields start_date and end_date are provided by the OCA
        # module account_invoice_start_end_dates
        if (
            ns["level"] in PROFILES_EN_UP
            and hasattr(iline, "start_date")
            and hasattr(iline, "end_date")
            and iline.start_date
            and iline.end_date
        ):
            bill_period = etree.SubElement(
                line_trade_settlement, ns["ram"] + "BillingSpecifiedPeriod"
            )
            self._cii_add_date("StartDateTime", iline.start_date, bill_period, ns)
            self._cii_add_date("EndDateTime", iline.end_date, bill_period, ns)

        subtotal = etree.SubElement(
            line_trade_settlement,
            ns["ram"] + "SpecifiedTradeSettlementLineMonetarySummation",
        )
        subtotal_amount = etree.SubElement(subtotal, ns["ram"] + "LineTotalAmount")
        subtotal_amount.text = "%0.*f" % (
            ns["cur_prec"],
            iline.price_subtotal * ns["sign"],
        )

    def generate_facturx_xml(self):
        self.ensure_one()
        assert self.type in (
            "out_invoice",
            "out_refund",
        ), "only works for customer invoice and refunds"
        dpo = self.env["decimal.precision"]
        level = self.company_id.facturx_level or "en16931"
        refund_type = self.company_id.facturx_refund_type or "381"
        sign = 1
        if self.type == "out_refund" and refund_type == "380":
            sign = -1
        nsmap = {
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "rsm": "urn:un:unece:uncefact:data:standard:" "CrossIndustryInvoice:100",
            "ram": "urn:un:unece:uncefact:data:standard:"
            "ReusableAggregateBusinessInformationEntity:100",
            "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
            "udt": "urn:un:unece:uncefact:data:" "standard:UnqualifiedDataType:100",
        }
        ns = {
            "rsm": "{urn:un:unece:uncefact:data:standard:" "CrossIndustryInvoice:100}",
            "ram": "{urn:un:unece:uncefact:data:standard:"
            "ReusableAggregateBusinessInformationEntity:100}",
            "qdt": "{urn:un:unece:uncefact:data:standard:" "QualifiedDataType:100}",
            "udt": "{urn:un:unece:uncefact:data:standard:" "UnqualifiedDataType:100}",
            "level": level,
            "refund_type": refund_type,
            "sign": sign,
            "currency": self.currency_id.name,
            "cur_prec": self.currency_id.decimal_places,
            "price_prec": dpo.precision_get("Product Price"),
            "disc_prec": dpo.precision_get("Discount"),
            "qty_prec": dpo.precision_get("Product Unit of Measure"),
        }

        root = etree.Element(ns["rsm"] + "CrossIndustryInvoice", nsmap=nsmap)
        self = self.with_context(
            lang=self.partner_id.lang or self.env.user.lang or "en_US"
        )
        self._cii_add_document_context_block(root, nsmap, ns)
        self._cii_add_header_block(root, ns)

        trade_transaction = etree.SubElement(
            root, ns["rsm"] + "SupplyChainTradeTransaction"
        )

        if ns["level"] in ("extended", "en16931", "basic"):
            line_number = 0
            for iline in self.invoice_line_ids.filtered(lambda x: not x.display_type):
                line_number += 1
                self._cii_add_invoice_line_block(
                    trade_transaction, iline, line_number, ns
                )

        self._cii_add_trade_agreement_block(trade_transaction, ns)
        self._cii_add_trade_delivery_block(trade_transaction, ns)
        self._cii_add_trade_settlement_block(trade_transaction, ns)

        xml_string = etree.tostring(
            root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )
        check_facturx_xsd(xml_string, "factur-x", facturx_level=ns["level"])
        logger.debug("Factur-X XML file generated for invoice ID %d", self.id)
        logger.debug(xml_string)
        return (xml_string, level)

    def _prepare_pdf_metadata(self):
        self.ensure_one()
        company_name = self.company_id.name
        inv_type = self.type == "out_refund" and _("Refund") or _("Invoice")
        pdf_metadata = {
            "author": company_name,
            "keywords": ", ".join([inv_type, _("Factur-X")]),
            "title": _("%s: %s %s dated %s")
            % (
                company_name,
                inv_type,
                self.name or self.state,
                self.invoice_date or "(no date)",
            ),
            "subject": "Factur-X %s %s dated %s issued by %s"
            % (
                inv_type,
                self.name or self.state,
                self.invoice_date or "(no date)",
                company_name,
            ),
        }
        return pdf_metadata

    def regular_pdf_invoice_to_facturx_invoice(self, pdf_content):
        self.ensure_one()
        assert pdf_content, "Missing pdf_content"
        if self.type in ("out_invoice", "out_refund"):
            facturx_xml_str, level = self.generate_facturx_xml()
            pdf_metadata = self._prepare_pdf_metadata()
            # Generate a new PDF with XML file as attachment
            pdf_content = generate_facturx_from_binary(
                pdf_content,
                facturx_xml_str,
                check_xsd=False,
                facturx_level=level,
                pdf_metadata=pdf_metadata,
            )
            logger.info("%s file added to PDF invoice", FACTURX_FILENAME)
        return pdf_content
