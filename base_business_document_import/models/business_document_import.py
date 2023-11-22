# Copyright 2015-2021 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from urllib.parse import urlparse

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

from odoo.addons.base_iban.models.res_partner_bank import validate_iban

logger = logging.getLogger(__name__)


class BusinessDocumentImport(models.AbstractModel):
    _name = "business.document.import"
    _description = "Common methods to import business documents"

    @api.model
    def user_error_wrap(self, method, data_dict, error_msg):
        """The method and data_dict arguments are useful when you want to
        inherit this method to update the error message"""
        assert error_msg
        raise UserError(error_msg)

    def _direct_match(self, data_dict, model, raise_exception=True):
        if data_dict.get("recordset"):
            record = data_dict["recordset"]
            if isinstance(record, type(model)):
                return record
            elif raise_exception:
                raise UserError(
                    _(
                        "The record '{record}' is an instance of '{record_model}', "
                        "not of '{target_model}'."
                    ).format(
                        record=record.display_name,
                        record_model=record._name,
                        target_model=model._name,
                    )
                )
        if data_dict.get("id"):
            record = False
            try:
                record = model.browse(data_dict["id"])
                # Browsing an unexisting ID doesn't make Odoo crash
                # So I read create_date to make it crash
                record.create_date  # pylint: disable=pointless-statement
            except Exception:
                if raise_exception:
                    raise UserError(
                        _("ID {id} of '{model}' doesn't exist in Odoo.").format(
                            id=data_dict["id"], model=model._name
                        )
                    )
            if record:
                return record
        if data_dict.get("xmlid"):
            xmlid = data_dict["xmlid"]
            record = False
            try:
                record = self.env.ref(xmlid, raise_if_not_found=True)
            except Exception:
                if raise_exception:
                    raise UserError(_("The XMLID '%s' doesn't exist in Odoo.") % xmlid)
            if record:
                if isinstance(record, type(model)):
                    return record
                elif raise_exception:
                    raise UserError(
                        _(
                            "The record '{record}' is an instance of '{record_model}', "
                            "not of '{target_model}'."
                        ).format(
                            record=record.display_name,
                            record_model=record._name,
                            target_model=model._name,
                        )
                    )
        return None

    @api.model
    def _strip_cleanup_dict(self, match_dict):
        if match_dict:
            for key, value in match_dict.items():
                if value and isinstance(value, str):
                    match_dict[key] = value.strip()
            if match_dict.get("country_code"):
                match_dict["country_code"] = match_dict["country_code"].upper()
            if match_dict.get("state_code"):
                match_dict["state_code"] = match_dict["state_code"].upper()

    @api.model
    def _get_match_partner_order(self, partner_type):
        if partner_type == "supplier":
            return "supplier_rank desc"
        if partner_type == "customer":
            return "customer_rank desc"
        return ""

    @api.model
    def _get_match_partner_type_label(self, partner_type):
        if partner_type == "supplier":
            return _("supplier")
        if partner_type == "customer":
            return _("customer")
        return _("partner")

    @api.model
    def _get_country_filter(self, partner_dict, chatter_msg):
        """Generate filter by country"""
        country = False
        if partner_dict.get("country_code"):
            country = self.env["res.country"].search(
                [("code", "=", partner_dict["country_code"])], limit=1
            )
            if country:
                return [
                    "|",
                    ("country_id", "=", False),
                    ("country_id", "=", country.id),
                ]
            chatter_msg.append(
                _(
                    "The analysis of the business document returned '%s' as "
                    "country code. But there are no country with that code "
                    "in Odoo."
                )
                % partner_dict["country_code"]
            )
        return False

    @api.model
    def _get_country_state_filter(self, partner_dict, chatter_msg):
        if partner_dict.get("state_code"):
            country = self.env["res.country"].search(
                [("code", "=", partner_dict["country_code"])], limit=1
            )
            state = self.env["res.country.state"].search(
                [
                    ("code", "=", partner_dict["state_code"]),
                    ("country_id", "=", country.id),
                ],
                limit=1,
            )
            if state:
                return ["|", ("state_id", "=", False), ("state_id", "=", state.id)]
        return False

    @api.model
    def _match_partner_ref(self, partner_dict, chatter_msg, domain, order):
        """If a ref is explicitly given, we just want to match that partner"""
        if partner_dict.get("ref"):
            return self.env["res.partner"].search(
                domain + [("ref", "=", partner_dict["ref"])], limit=1, order=order
            )
        return False

    @api.model
    def _match_partner_contact(self, partner_dict, chatter_msg, domain, order):
        rpo = self.env["res.partner"]
        if partner_dict.get("email") and "@" in partner_dict["email"]:
            partner = rpo.search(
                domain + [("email", "=ilike", partner_dict["email"])],
                limit=1,
                order=order,
            )
            if partner:
                return partner
        if partner_dict.get("contact"):
            partner = rpo.search(
                domain + [("name", "=ilike", partner_dict["contact"])],
                limit=1,
                order=order,
            )
            if partner:
                return partner
        if partner_dict.get("phone"):
            partner = rpo.search(
                domain
                + [
                    "|",
                    ("mobile", "=", partner_dict["phone"]),
                    ("phone", "=", partner_dict["phone"]),
                ],
                limit=1,
                order=order,
            )
            if partner:
                return partner
        return False

    @api.model
    def _match_partner_name(self, partner_dict, chatter_msg, domain, order):
        if partner_dict.get("name"):
            return self.env["res.partner"].search(
                domain + [("name", "=ilike", partner_dict["name"])],
                limit=1,
                order=order,
            )
        return False

    @api.model
    def _get_partner_website_domain(self, partner_dict):
        if partner_dict.get("website"):
            urlp = urlparse(partner_dict["website"])
            netloc = urlp.netloc
            if not urlp.scheme and not netloc:
                netloc = urlp.path
            if netloc and len(netloc.split(".")) >= 2:
                return ".".join(netloc.split(".")[-2:])
        return False

    @api.model
    def _match_partner_website(self, partner_dict, chatter_msg, domain, order):
        website_domain = self._get_partner_website_domain(partner_dict)
        if website_domain:
            return self.env["res.partner"].search(
                domain + [("website", "=ilike", "%" + website_domain + "%")],
                limit=1,
                order=order,
            )
        return False

    @api.model
    def _get_partner_email_domain(self, partner_dict):
        return (
            partner_dict.get("email")
            and "@" in partner_dict["email"]
            and partner_dict["email"].split("@")[1]
        )

    @api.model
    def _match_partner_email(self, partner_dict, chatter_msg, domain, order):
        email_domain = self._get_partner_email_domain(partner_dict)
        # I can't search on email addresses with
        # email_domain because of the emails such as
        # @gmail.com, @yahoo.com that may match random partners
        if email_domain:
            partner = self.env["res.partner"].search(
                domain + [("website", "=ilike", "%" + email_domain + "%")],
                limit=1,
                order=order,
            )
            if not partner:
                partner = self.env["res.partner"].search(
                    domain + [("email", "=ilike", "%@" + email_domain)],
                    limit=1,
                    order=order,
                )
            if partner:
                partner_type_label = partner_dict["type_label"]
                chatter_msg.append(
                    _(
                        "The %s has been identified by the domain name '%s' "
                        "so please check carefully that the %s is correct."
                    )
                    % (partner_type_label, domain, partner_type_label)
                )
                return partner

    @api.model
    def _match_partner(  # noqa: C901
        self,
        partner_dict,
        chatter_msg,
        partner_type="supplier",
        domain=None,
        raise_exception=True,
    ):
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
        """
        rpo = self.env["res.partner"]
        partner_dict = partner_dict.copy()
        self._strip_cleanup_dict(partner_dict)
        partner = self._direct_match(partner_dict, rpo, raise_exception=raise_exception)
        if partner:
            return partner
        domain = domain or []
        domain += self._match_company_domain()
        order = self._get_match_partner_order(partner_type)
        partner_type_label = self._get_match_partner_type_label(partner_type)
        partner_dict["type"] = partner_type
        partner_dict["type_label"] = partner_type_label

        partner = self._match_partner_ref(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        country_domain = self._get_country_filter(partner_dict, chatter_msg)

        if country_domain:
            domain += country_domain

            state_domain = self._get_country_state_filter(partner_dict, chatter_msg)
            if state_domain:
                domain += state_domain

        # Search on VAT
        if partner_dict.get("vat"):
            vat = partner_dict["vat"].replace(" ", "").upper()
            partner = rpo.search(domain + [("vat", "=", vat)], limit=1, order=order)
            if partner:
                return partner

        # Hook to plug alternative matching methods
        partner = self._hook_match_partner(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        # Search for partner contact
        partner = self._match_partner_contact(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        # Search for partner name
        partner = self._match_partner_name(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        # Search for partner website
        partner = self._match_partner_website(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        # Search for partner website
        partner = self._match_partner_email(partner_dict, chatter_msg, domain, order)
        if partner:
            return partner

        if not raise_exception:
            return None
        raise self.user_error_wrap(
            "_match_partner",
            partner_dict,
            _(
                "Odoo couldn't find any %s corresponding to the following "
                "information extracted from the business document:\n"
                "Name: %s\n"
                "VAT number: %s\n"
                "Reference: %s\n"
                "E-mail: %s\n"
                "Website: %s\n"
                "State code: %s\n"
                "Country code: %s\n"
            )
            % (
                partner_type_label,
                partner_dict.get("name") or "",
                partner_dict.get("vat") or "",
                partner_dict.get("ref") or "",
                partner_dict.get("email") or "",
                partner_dict.get("website") or "",
                partner_dict.get("state_code") or "",
                partner_dict.get("country_code") or "",
            ),
        )

    @api.model
    def _hook_match_partner(self, partner_dict, chatter_msg, domain, order):
        return False

    @api.model
    def _match_shipping_partner(
        self, partner_dict, partner, chatter_msg, domain=None, raise_exception=True
    ):
        """Example:
        shipping_dict = {
            'email': 'contact@akretion.com',
            'name': 'Akretion France',
            'street': 'Long Avenue',
            'street2': 'Building 2A',
            'city': 'Paris',
            'zip': '69100',
            'country_code': 'FR',
            }
        The shipping partner can be any partner, not especially related to the
        customer/supplier (partner argument)
        """
        domain = domain or []
        if partner_dict.get("street"):
            if partner_dict.get("street_number"):
                domain += [
                    (
                        "street",
                        "in",
                        [
                            "{} {}".format(
                                partner_dict.get("street"),
                                partner_dict.get("street_number"),
                            ),
                            "{} {}".format(
                                partner_dict.get("street_number"),
                                partner_dict.get("street"),
                            ),
                            "{}, {}".format(
                                partner_dict.get("street"),
                                partner_dict.get("street_number"),
                            ),
                            "{}, {}".format(
                                partner_dict.get("street_number"),
                                partner_dict.get("street"),
                            ),
                        ],
                    )
                ]
            else:
                domain += [("street", "=", partner_dict.get("street"))]
        if partner_dict.get("street2"):
            domain += [("street2", "=", partner_dict.get("street2"))]
        if partner_dict.get("city"):
            domain += [("city", "=", partner_dict.get("city"))]
        if partner_dict.get("zip"):
            domain += [("zip", "=", partner_dict.get("zip"))]

        domain_delivery = domain + [("type", "=", "delivery")]
        partner = self._match_partner(
            partner_dict,
            chatter_msg,
            partner_type=False,
            domain=domain_delivery,
            raise_exception=False,
        )
        if partner:
            return partner
        if not partner_dict.get("vat") and not partner_dict.get("email"):
            partner = self.env["res.partner"].search(domain_delivery, limit=1)
        if partner:
            return partner
        partner = self._match_partner(
            partner_dict,
            chatter_msg,
            partner_type=False,
            domain=domain,
            raise_exception=False,
        )
        if partner:
            return partner
        if not partner_dict.get("vat"):
            partner = self.env["res.partner"].search(domain, limit=1)
        if partner:
            return partner

        if not raise_exception:
            return
        raise self.user_error_wrap(
            "_match_shipping_partner",
            partner_dict,
            _(
                "Odoo couldn't find any shipping partner corresponding to the "
                "following information extracted from the business document:\n"
                "Name: %s\n"
                "VAT number: %s\n"
                "Reference: %s\n"
                "E-mail: %s\n"
                "Website: %s\n"
                "Street: %s\n"
                "Street2: %s\n"
                "City: %s\n"
                "ZIP: %s\n"
                "State code: %s\n"
                "Country code: %s\n"
            )
            % (
                partner_dict.get("name") or "",
                partner_dict.get("vat") or "",
                partner_dict.get("ref") or "",
                partner_dict.get("email") or "",
                partner_dict.get("website") or "",
                partner_dict.get("street") or "",
                partner_dict.get("street2") or "",
                partner_dict.get("city") or "",
                partner_dict.get("zip") or "",
                partner_dict.get("state_code") or "",
                partner_dict.get("country_code") or "",
            ),
        )

    @api.model
    def _match_partner_bank(
        self, partner, iban, bic, chatter_msg, create_if_not_found=False
    ):
        assert iban, "iban is a required arg"
        assert partner, "partner is a required arg"
        partner = partner.commercial_partner_id
        iban = iban.replace(" ", "").upper()
        rpbo = self.env["res.partner.bank"]
        rbo = self.env["res.bank"]
        try:
            validate_iban(iban)
        except Exception:
            chatter_msg.append(
                _("IBAN <b>%s</b> is not valid, so it has been ignored.") % iban
            )
            return False
        bankaccount = rpbo.search(
            self._match_company_domain()
            + [
                ("sanitized_acc_number", "=", iban),
                ("partner_id", "=", partner.id),
            ],
            limit=1,
        )
        if bankaccount:
            return bankaccount
        elif create_if_not_found:
            bank_id = False
            if bic:
                bic = bic.replace(" ", "").upper()
                bank = rbo.search([("bic", "=", bic)], limit=1)
                if bank:
                    bank_id = bank.id
                else:
                    bank = rbo.create(
                        {"bic": bic, "name": bic}  # TODO: see if we could do better
                    )
                    bank_id = bank.id
            partner_bank = rpbo.create(
                {"partner_id": partner.id, "acc_number": iban, "bank_id": bank_id}
            )
            chatter_msg.append(
                _(
                    "The bank account <b>IBAN %s</b> has been automatically "
                    "added on the supplier "
                    "<a href=# data-oe-model=res.partner data-oe-id=%d>%s</a>"
                )
                % (iban, partner.id, partner.display_name)
            )
            return partner_bank
        else:
            chatter_msg.append(
                _(
                    "The analysis of the business document returned "
                    "<b>IBAN %s</b> as bank account, but there is no such "
                    "bank account in Odoo linked to partner "
                    "<a href=# data-oe-model=res.partner data-oe-id=%d>%s</a> and "
                    "the option to automatically create bank "
                    "accounts upon import is disabled."
                )
                % (iban, partner.id, partner.display_name)
            )

    @api.model
    def _match_product(self, product_dict, chatter_msg, seller=False):
        """Retrieve product.

        Matching sequence:

        1. ID
        2. barcode
        3. packaging barcode
        4. default_code
        5. seller code

        :param product_dict: dictionary w/ product info.

            Example: {'barcode': '5449000054227', 'code': 'COCA1L'}

        :param chatter_msg: list of msgs to append to chatter (if any)
        :param seller: optional product.supplierinfo record
        """
        ppo = self.env["product.product"]
        self._strip_cleanup_dict(product_dict)
        product = self._direct_match(product_dict, ppo)
        if product:
            return product
        product = self._match_product_search(product_dict)
        if product:
            return product
        elif seller:
            # WARNING: Won't work for multi-variant products
            # because product.supplierinfo is attached to product template
            sinfo = self.env["product.supplierinfo"].search(
                self._match_company_domain()
                + [
                    ("name", "=", seller.id),
                    ("product_code", "=", product_dict["code"]),
                ],
                limit=1,
            )
            if (
                sinfo
                and sinfo.product_tmpl_id.product_variant_ids
                and len(sinfo.product_tmpl_id.product_variant_ids) == 1
            ):
                return sinfo.product_tmpl_id.product_variant_ids[0]
        raise self.user_error_wrap(
            "_match_product",
            product_dict,
            _(
                "Odoo couldn't find any product corresponding to the "
                "following information extracted from the business document:\n"
                "Barcode: %s\n"
                "Product code: %s\n"
                "Supplier: %s\n"
            )
            % (
                product_dict.get("barcode") or "",
                product_dict.get("code") or "",
                seller and seller.name or "",
            ),
        )

    @api.model
    def _match_product_search(self, product_dict):
        product = self.env["product.product"].browse()
        cdomain = self._match_company_domain()
        if product_dict.get("barcode"):
            domain = cdomain + [
                "|",
                ("barcode", "=", product_dict["barcode"]),
                ("packaging_ids.barcode", "=", product_dict["barcode"]),
            ]
            product = product.search(domain, limit=1)
        if not product and product_dict.get("code"):
            # TODO: this domain could be probably included in the former one
            domain = cdomain + [
                "|",
                ("barcode", "=", product_dict["code"]),
                ("default_code", "=", product_dict["code"]),
            ]
            product = product.search(domain, limit=1)
        return product

    @api.model
    def _match_company_domain(self):
        company_id = self._context.get("force_company") or self.env.company.id
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]

    @api.model
    def _match_currency(self, currency_dict, chatter_msg):
        """Example:
        currency_dict = {
            'iso': 'USD',  # If we have ISO, no need to have more keys
            'symbol': '$',
            'country_code': 'US',
            'iso_or_symbol': '$',
            }
        """
        if not currency_dict:
            currency_dict = {}
        rco = self.env["res.currency"]
        self._strip_cleanup_dict(currency_dict)
        currency = self._direct_match(currency_dict, rco)
        if currency:
            return currency
        if currency_dict.get("iso"):
            currency_iso = currency_dict["iso"].upper()
            currency = rco.search([("name", "=", currency_iso)], limit=1)
            if currency:
                return currency
            else:
                raise self.user_error_wrap(
                    "_match_currency",
                    currency_dict,
                    _(
                        "The analysis of the business document returned '%s' as "
                        "the currency ISO code. But there are no currency "
                        "with that code in Odoo."
                    )
                    % currency_iso,
                )
        if currency_dict.get("symbol"):
            currencies = rco.search([("symbol", "=", currency_dict["symbol"])])
            if len(currencies) == 1:
                return currencies[0]
            else:
                chatter_msg.append(
                    _(
                        "The analysis of the business document returned '%s' as "
                        "the currency symbol. But there are none or several "
                        "currencies with that symbol in Odoo."
                    )
                    % currency_dict["symbol"]
                )
        if currency_dict.get("iso_or_symbol"):
            currencies = rco.search(
                [
                    "|",
                    ("name", "=", currency_dict["iso_or_symbol"].upper()),
                    ("symbol", "=", currency_dict["iso_or_symbol"]),
                ]
            )
            if len(currencies) == 1:
                return currencies[0]
            else:
                raise self.user_error_wrap(
                    "_match_currency",
                    currency_dict,
                    _(
                        "The analysis of the business document returned '%s' as "
                        "the currency symbol or ISO code. But there are none or "
                        "several currencies with the symbol/ISO code in Odoo."
                    )
                    % currency_dict["iso_or_symbol"],
                )
        if currency_dict.get("country_code"):
            country_code = currency_dict["country_code"]
            country = self.env["res.country"].search(
                [("code", "=", country_code)], limit=1
            )
            if country:
                if country.currency_id:
                    return country.currency_id
                else:
                    raise self.user_error_wrap(
                        "_match_currency",
                        currency_dict,
                        _(
                            "The analysis of the business document returned '%s' "
                            "as the country code to find the related currency. "
                            "But the country '%s' doesn't have any related "
                            "currency configured in Odoo."
                        )
                        % (country_code, country.name),
                    )
            else:
                raise self.user_error_wrap(
                    "_match_currency",
                    currency_dict,
                    _(
                        "The analysis of the business document returned '%s' "
                        "as the country code to find the related currency. "
                        "But there is no country with that code in Odoo."
                    )
                    % country_code,
                )
        if self._context.get("force_company"):
            company = self.env["res.company"].browse(self._context["force_company"])
        else:
            company = self.env.company
        company_cur = company.currency_id
        chatter_msg.append(
            _("No currency specified, so Odoo used the company currency (%s)")
            % company_cur.name
        )
        return company_cur

    @api.model
    def _match_uom(self, uom_dict, chatter_msg, product=False):
        """Example:
        uom_dict = {
            'unece_code': 'LTR',
            'name': 'Liter',
            }
        """
        uuo = self.env["uom.uom"]
        if not uom_dict:
            uom_dict = {}
        self._strip_cleanup_dict(uom_dict)
        uom = self._direct_match(uom_dict, uuo)
        if uom:
            return uom
        if uom_dict.get("unece_code"):
            # Map NIU to Unit
            if uom_dict["unece_code"] == "NIU":
                uom_dict["unece_code"] = "C62"
            uom = uuo.search([("unece_code", "=", uom_dict["unece_code"])], limit=1)
            if uom:
                return uom
            else:
                chatter_msg.append(
                    _(
                        "The analysis of the business document returned '%s' "
                        "as the unit of measure UNECE code, but there is no "
                        "unit of measure with that UNECE code in Odoo. Please "
                        "check the configuration of the units of measures in "
                        "Odoo."
                    )
                    % uom_dict["unece_code"]
                )
        if uom_dict.get("name"):
            uom = uuo.search([("name", "=ilike", uom_dict["name"] + "%")], limit=1)
            if uom:
                return uom
        if product:
            return product.uom_id
        chatter_msg.append(
            _(
                "<p>Odoo couldn't find any unit of measure corresponding to the "
                "following information extracted from the business document:</p>"
                "<ul><li>UNECE code: %s</li>"
                "<li>Name of the unit of measure: %s</li></ul>"
                "<p>So the unit of measure 'Unit(s)' has been used. <em>You may "
                "have to change it manually.</em></p>"
            )
            % (uom_dict.get("unece_code"), uom_dict.get("name"))
        )
        return self.env.ref("uom.product_uom_unit")

    @api.model
    def _match_taxes(
        self, taxes_list, chatter_msg, type_tax_use="purchase", price_include=False
    ):
        """taxes_list must be a list of tax_dict"""
        taxes_recordset = self.env["account.tax"].browse(False)
        for tax_dict in taxes_list:
            taxes_recordset += self._match_tax(
                tax_dict,
                chatter_msg,
                type_tax_use=type_tax_use,
                price_include=tax_dict.get("price_include", price_include),
            )
        return taxes_recordset

    @api.model
    def _prepare_match_tax_domain(
        self, tax_dict, type_tax_use="purchase", price_include=False
    ):
        ato = self.env["account.tax"]
        company_id = self._context.get("force_company") or self.env.company.id
        domain = [("company_id", "=", company_id)]
        if type_tax_use == "purchase":
            domain.append(("type_tax_use", "=", "purchase"))
        elif type_tax_use == "sale":
            domain.append(("type_tax_use", "=", "sale"))
        if price_include is False:
            domain.append(("price_include", "=", False))
        elif price_include is True:
            domain.append(("price_include", "=", True))
        # with the code above, if you set price_include=None, it will
        # won't depend on the value of the price_include parameter
        assert tax_dict.get("amount_type") in [
            "fixed",
            "percent",
        ], "bad tax type, has to be fixed or percent"
        assert "amount" in tax_dict, "Missing amount key in tax_dict"
        domain.append(("amount_type", "=", tax_dict["amount_type"]))
        if tax_dict.get("unece_type_code"):
            domain.append(("unece_type_code", "=", tax_dict["unece_type_code"]))
        if tax_dict.get("unece_categ_code"):
            domain.append(("unece_categ_code", "=", tax_dict["unece_categ_code"]))
        if tax_dict.get("unece_due_date_code"):
            tax_exigibility = ato._get_tax_exigibility_from_unece_code(
                tax_dict["unece_due_date_code"]
            )
            if tax_exigibility:
                domain += [("tax_exigibility", "=", tax_exigibility)]
        return domain

    @api.model
    def _match_tax(
        self,
        tax_dict,
        chatter_msg,
        type_tax_use="purchase",
        price_include=False,
    ):
        """Example:
        tax_dict = {
            'amount_type': 'percent',  # required param, 'fixed' or 'percent'
            'amount': 20.0,  # required
            'unece_type_code': 'VAT',
            'unece_categ_code': 'S',
            'unece_due_date_code': '72',
            }
        """
        ato = self.env["account.tax"]
        self._strip_cleanup_dict(tax_dict)
        tax = self._direct_match(tax_dict, ato)
        if tax:
            return tax
        domain = self._prepare_match_tax_domain(
            tax_dict, type_tax_use=type_tax_use, price_include=price_include
        )
        taxes = ato.search(domain)
        for tax in taxes:
            tax_amount = tax.amount  # 'amount' field : digits=(16, 4)
            if not float_compare(tax_dict["amount"], tax_amount, precision_digits=4):
                return tax
        raise self.user_error_wrap(
            "_match_tax",
            tax_dict,
            _(
                "Odoo couldn't find any tax with 'Tax Application' = '%s' "
                "and 'Tax Included in Price' = '%s' which correspond to the "
                "following information extracted from the business document:\n"
                "UNECE Tax Type code: %s\n"
                "UNECE Tax Category code: %s\n"
                "UNECE Due Date code: %s\n"
                "Tax amount: %s %s"
            )
            % (
                type_tax_use,
                price_include,
                tax_dict.get("unece_type_code") or "",
                tax_dict.get("unece_categ_code") or "",
                tax_dict.get("unece_due_date_code") or "",
                tax_dict["amount"],
                tax_dict["amount_type"] == "percent" and "%" or _("(fixed)"),
            ),
        )

    def compare_lines(
        self,
        existing_lines,
        import_lines,
        chatter_msg,
        qty_precision=None,
        price_precision=None,
        seller=False,
    ):
        """Example:
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
        dpo = self.env["decimal.precision"]
        if qty_precision is None:
            qty_precision = dpo.precision_get("Product Unit of Measure")
        if price_precision is None:
            price_precision = dpo.precision_get("Product Price")
        existing_lines_dict = {}
        for eline in existing_lines:
            if not eline.get("product"):
                chatter_msg.append(
                    _(
                        "The existing line '%s' doesn't have any product, "
                        "so <b>the lines haven't been updated</b>."
                    )
                    % eline.get("name")
                )
                return False
            if eline["product"] in existing_lines_dict:
                chatter_msg.append(
                    _(
                        "The product '%s' is used on several existing "
                        "lines, so <b>the lines haven't been updated</b>."
                    )
                    % eline["product"].display_name
                )
                return False
            existing_lines_dict[eline["product"]] = eline
        unique_import_products = []
        res = {
            "to_remove": False,
            "to_add": [],
            "to_update": {},
        }
        for iline in import_lines:
            if not iline.get("product"):
                chatter_msg.append(
                    _(
                        "One of the imported lines doesn't have any product, "
                        "so <b>the lines haven't been updated</b>."
                    )
                )
                return False
            product = self._match_product(iline["product"], chatter_msg, seller=seller)
            uom = self._match_uom(iline.get("uom"), chatter_msg, product)
            if product in unique_import_products:
                chatter_msg.append(
                    _(
                        "The product '%s' is used on several imported lines, "
                        "so <b>the lines haven't been updated</b>."
                    )
                    % product.display_name
                )
                return False
            unique_import_products.append(product)
            if product in existing_lines_dict:
                if uom != existing_lines_dict[product]["uom"]:
                    chatter_msg.append(
                        _(
                            "For product '%s', the unit of measure is %s on the "
                            "existing line, but it is %s on the imported line. "
                            "We don't support this scenario for the moment, so "
                            "<b>the lines haven't been updated</b>."
                        )
                        % (
                            product.display_name,
                            existing_lines_dict[product]["uom"].name,
                            uom.name,
                        )
                    )
                    return False
                # used for to_remove
                existing_lines_dict[product]["import"] = True
                oline = existing_lines_dict[product]["line"]
                res["to_update"][oline] = self._prepare_order_line_update_values(
                    existing_lines_dict[product], iline, qty_precision, price_precision
                )
            else:
                res["to_add"].append(
                    {"product": product, "uom": uom, "import_line": iline}
                )
        for exiting_dict in existing_lines_dict.values():
            if not exiting_dict.get("import"):
                if res["to_remove"]:
                    res["to_remove"] += exiting_dict["line"]
                else:
                    res["to_remove"] = exiting_dict["line"]
        return res

    def _prepare_order_line_update_values(
        self, existing_line, iline, qty_precision, price_precision
    ):
        values = {}
        if float_compare(
            iline["qty"],
            existing_line["qty"],
            precision_digits=qty_precision,
        ):
            values["qty"] = [existing_line["qty"], iline["qty"]]
        if "price_unit" in iline and float_compare(
            iline["price_unit"],
            existing_line["price_unit"],
            precision_digits=price_precision,
        ):
            values["price_unit"] = [
                existing_line["price_unit"],
                iline["price_unit"],
            ]
        return values

    def _prepare_account_speed_dict(self):
        company_id = self._context.get("force_company") or self.env.company.id
        res = self.env["account.account"].search_read(
            [("company_id", "=", company_id), ("deprecated", "=", False)], ["code"]
        )
        speed_dict = {}
        for line in res:
            speed_dict[line["code"].upper()] = line["id"]
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
        aao = self.env["account.account"]
        if speed_dict is None:
            speed_dict = self._prepare_account_speed_dict()
        self._strip_cleanup_dict(account_dict)
        account = self._direct_match(account_dict, aao)
        if account:
            return account
        if account_dict.get("code"):
            acc_code = account_dict["code"].upper()
            if acc_code in speed_dict:
                return aao.browse(speed_dict[acc_code])
            # Match when account_dict['code'] is longer than Odoo's account
            # codes because of trailing '0'
            # I don't think we need a warning for this kind of match
            acc_code_tmp = acc_code
            while acc_code_tmp and acc_code_tmp[-1] == "0":
                acc_code_tmp = acc_code_tmp[:-1]
                if acc_code_tmp and acc_code_tmp in speed_dict:
                    return aao.browse(speed_dict[acc_code_tmp])
            # Match when account_dict['code'] is shorter than Odoo's accounts
            # -> warns the user about this
            for code, account_id in speed_dict.items():
                if code.startswith(acc_code):
                    chatter_msg.append(
                        _(
                            "Approximate match: account %s has been matched "
                            "with account %s"
                        )
                        % (account_dict["code"], code)
                    )
                    return aao.browse(account_id)
        raise self.user_error_wrap(
            "_match_account",
            account_dict,
            _(
                "Odoo couldn't find any account corresponding to the "
                "following information extracted from the business document:\n"
                "Account code: %s"
            )
            % (account_dict.get("code") or ""),
        )

    def _prepare_analytic_account_speed_dict(self):
        company_id = self._context.get("force_company") or self.env.company.id
        res = self.env["account.analytic.account"].search_read(
            [("company_id", "=", company_id)], ["code"]
        )
        speed_dict = {}
        for line in res:
            if line["code"]:
                speed_dict[line["code"].upper()] = line["id"]
        return speed_dict

    @api.model
    def _match_analytic_account(self, aaccount_dict, chatter_msg, speed_dict=None):
        """Example:
        aaccount_dict = {
            'code': '627',
            }
        speed_dict is usefull to gain performance when you have a lot of
        analytic accounts to match
        """
        if not aaccount_dict:
            aaccount_dict = {}
        aaao = self.env["account.analytic.account"]
        if speed_dict is None:
            speed_dict = self._prepare_analytic_account_speed_dict()
        self._strip_cleanup_dict(aaccount_dict)
        aaccount = self._direct_match(aaccount_dict, aaao)
        if aaccount:
            return aaccount
        if aaccount_dict.get("code"):
            aacode = aaccount_dict["code"].upper()
            if aacode in speed_dict:
                return aaao.browse(speed_dict[aacode])
        raise self.user_error_wrap(
            "_match_analytic_account",
            aaccount_dict,
            _(
                "Odoo couldn't find any analytic account corresponding to the "
                "following information extracted from the business document:\n"
                "Analytic account code: %s"
            )
            % (aaccount_dict.get("code") or ""),
        )

    def _prepare_journal_speed_dict(self):
        company_id = self._context.get("force_company") or self.env.company.id
        res = self.env["account.journal"].search_read(
            [("company_id", "=", company_id)], ["code"]
        )
        speed_dict = {}
        for line in res:
            speed_dict[line["code"].upper()] = line["id"]
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
        ajo = self.env["account.journal"]
        if speed_dict is None:
            speed_dict = self._prepare_journal_speed_dict()
        self._strip_cleanup_dict(journal_dict)
        journal = self._direct_match(journal_dict, ajo)
        if journal:
            return journal
        if journal_dict.get("code"):
            jcode = journal_dict["code"].upper()
            if jcode in speed_dict:
                return ajo.browse(speed_dict[jcode])
            # case insensitive
        raise self.user_error_wrap(
            "_match_journal",
            journal_dict,
            _(
                "Odoo couldn't find any journal corresponding to the "
                "following information extracted from the business document:\n"
                "Journal code: %s"
            )
            % (journal_dict.get("code") or ""),
        )

    # Code moved from base_business_document_import_stock
    # Now that the incoterm obj (account.incoterms) is defined in
    # the 'account' module (since Odoo v12) instead of 'stock'
    @api.model
    def _match_incoterm(self, incoterm_dict, chatter_msg):
        aio = self.env["account.incoterms"]
        if not incoterm_dict:
            incoterm_dict = {}
        self._strip_cleanup_dict(incoterm_dict)
        incoterm = self._direct_match(incoterm_dict, aio)
        if incoterm:
            return incoterm
        if incoterm_dict.get("code"):
            incoterm = aio.search(
                [
                    "|",
                    ("name", "=ilike", incoterm_dict["code"]),
                    ("code", "=ilike", incoterm_dict["code"]),
                ],
                limit=1,
            )
            if incoterm:
                return incoterm
            else:
                self.user_error_wrap(
                    "_match_incoterm",
                    incoterm_dict,
                    _("Could not find any Incoterm in Odoo corresponding " "to '%s'")
                    % incoterm_dict["code"],
                )
        return False

    @api.model
    def _check_company(self, company_dict, chatter_msg):
        if not company_dict:
            company_dict = {}
        rco = self.env["res.company"]
        if self._context.get("force_company"):
            company = rco.browse(self._context["force_company"])
        else:
            company = self.env.company
        if company_dict.get("vat"):
            parsed_company_vat = company_dict["vat"].replace(" ", "").upper()
            if company.partner_id.vat:
                if company.partner_id.vat != parsed_company_vat:
                    raise self.user_error_wrap(
                        "_check_company",
                        company_dict,
                        _(
                            "The VAT number of the customer written in the "
                            "business document (%s) doesn't match the VAT number "
                            "of the company '%s' (%s) in which you are trying to "
                            "import this document."
                        )
                        % (
                            parsed_company_vat,
                            company.display_name,
                            company.partner_id.vat,
                        ),
                    )
            else:
                chatter_msg.append(
                    _("Missing VAT number on company '%s'") % company.display_name
                )

    def get_xml_files_from_pdf(self, pdf_file):
        """Returns a dict with key = filename, value = XML file obj"""
        logger.warning(
            "`get_xml_files_from_pdf` deprecated: use `pdf.helper.pdf_get_xml_files`"
        )
        return self.env["pdf.helper"].pdf_get_xml_files(pdf_file)

    @api.model
    def post_create_or_update(self, parsed_dict, record, doc_filename=None):
        if parsed_dict.get("attachments"):
            for filename, data_base64 in parsed_dict["attachments"].items():
                self.env["ir.attachment"].create(
                    {
                        "name": filename,
                        "res_id": record.id,
                        "res_model": str(record._name),
                        "datas": data_base64,
                    }
                )
        for msg in parsed_dict["chatter_msg"]:
            record.message_post(body=msg)
        if parsed_dict.get("note"):
            if doc_filename:
                msg = _("<b>Notes in file %s:</b>") % doc_filename
            else:
                msg = _("<b>Notes in imported document:</b>")
            record.message_post(  # pylint: disable=translation-required
                body="{} {}".format(msg, parsed_dict["note"])
            )
