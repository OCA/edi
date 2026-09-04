# Copyright 2026 ACSONE SA/NV,BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv.expression import AND


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    def _get_tax_exemption_reason_code(self, tax_exemption_reason_code):
        """
        Map a UBL tax exemption reason code to a valid selection key for
        ubl_cii_tax_exemption_reason_code field

        handles formatting differences (e.g. '_' vs '-') by trying normalized
        variants of the input code

        :return: matching selection key or False if not found
        """
        tax_exemption_reason_codes = dict(
            self.env["account.tax"]
            ._fields.get("ubl_cii_tax_exemption_reason_code")
            .selection
        )
        if tax_exemption_reason_codes.get(tax_exemption_reason_code):
            return tax_exemption_reason_code
        if tax_exemption_reason_codes.get(tax_exemption_reason_code.replace("-", "_")):
            return tax_exemption_reason_code.replace("-", "_")
        if tax_exemption_reason_codes.get(tax_exemption_reason_code.replace("_", "-")):
            return tax_exemption_reason_code.replace("_", "-")
        return False

    def _import_ubl_invoice_line_prepare_classified_tax_category_tax_values(
        self, collected_values, tax_category_tree
    ):
        res = super()._import_ubl_invoice_line_prepare_classified_tax_category_tax_values(
            collected_values, tax_category_tree
        )

        # FIXME: inject VATEX code in res
        # FIXME: hook retrieve tax predictive, however there is no nice hook to process that code
        return res

        tax_amount = tax_category_tree.findtext("./{*}Percent")
        tax_unece_code = tax_category_tree.findtext("./{*}ID")
        if tax_amount is None or tax_unece_code is None:
            # stop if the file doesn't provide the UNECE tax code
            return res

        amount = float(tax_amount)

        invoice = collected_values.get("invoice")
        if not invoice:
            return res

        if invoice.journal_id.type != "purchase":
            # this addon targets purchase imports only
            return res

        tax_type = tax_category_tree.findtext("./{*}TaxScheme/{*}ID")
        if tax_type is None or tax_type.upper() != "VAT":
            return res

        tax_exemption_reason_code = tax_category_tree.findtext(
            "./{*}TaxExemptionReasonCode"
        )
        if tax_exemption_reason_code is not None:
            tax_exemption_reason_code = self._get_tax_exemption_reason_code(
                tax_exemption_reason_code
            )
        if (
            invoice_line.tax_ids.amount == amount
            and invoice_line.tax_ids.ubl_cii_tax_category_code == tax_unece_code
            and invoice_line.tax_ids.ubl_cii_tax_exemption_reason_code
            == tax_exemption_reason_code
        ):
            # stop if the result already matches the UNECE code
            return res
        taxes = self._get_tax_by_ubl_values(
            invoice.journal_id,
            amount,
            tax_unece_code,
            tax_exemption_reason_code=tax_exemption_reason_code,
        )
        if taxes:
            invoice_line.tax_ids = taxes[0]
        return res

    def _get_tax_by_ubl_values(
        self, journal, amount, tax_unece_code, tax_exemption_reason_code=False, **kwargs
    ):
        return self.env["account.tax"].search(
            self._get_tax_by_ubl_values_domain(
                journal, amount, tax_unece_code, tax_exemption_reason_code
            )
        )

    def _get_tax_by_ubl_values_domain(
        self, journal, amount, tax_unece_code, tax_exemption_reason_code=False
    ):
        domain = [
            ("company_id", "=", journal.company_id.id),
            ("amount_type", "=", "percent"),
            ("type_tax_use", "=", journal.type),
            ("ubl_cii_tax_category_code", "=", tax_unece_code),
            ("amount", "=", amount),
        ]
        if tax_exemption_reason_code:
            domain = AND(
                [
                    domain,
                    [
                        (
                            "ubl_cii_tax_exemption_reason_code",
                            "=",
                            tax_exemption_reason_code,
                        )
                    ],
                ]
            )
        return domain
