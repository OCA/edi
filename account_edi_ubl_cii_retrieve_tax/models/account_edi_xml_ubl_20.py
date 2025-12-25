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

    def _import_fill_invoice_line_form(
        self, journal, tree, invoice, invoice_line, qty_factor
    ):
        res = super()._import_fill_invoice_line_form(
            journal, tree, invoice, invoice_line, qty_factor
        )
        if journal.type != "purchase" or len(invoice_line.tax_ids) > 1:
            # this addon targets purchase imports only
            # UBL are expected to produce a single tax per line, if multiple taxes
            # were already assigned, keep the standard result to avoid unexpected
            # changes
            return res
        tax_type = tree.find(".//{*}Item/{*}ClassifiedTaxCategory/{*}TaxScheme/{*}ID")
        if tax_type is None or not tax_type.text or tax_type.text.upper() != "VAT":
            return res
        tax_unece_code_node = tree.find(".//{*}Item/{*}ClassifiedTaxCategory/{*}ID")
        tax_exemption_reason_code_node = tree.find(
            ".//{*}Item/{*}ClassifiedTaxCategory/{*}TaxExemptionReasonCode"
        )
        tax_exemption_reason_code = False
        if tax_exemption_reason_code_node is not None:
            tax_exemption_reason_code = self._get_tax_exemption_reason_code(
                tax_exemption_reason_code_node.text
            )
        tax_amount_node = tree.find(".//{*}Item/{*}ClassifiedTaxCategory/{*}Percent")
        if tax_amount_node is None or tax_unece_code_node is None:
            # stop if the file doesn't provide the UNECE tax code
            return res
        amount = float(tax_amount_node.text)
        tax_unece_code = tax_unece_code_node.text
        if (
            invoice_line.tax_ids.amount == amount
            and invoice_line.tax_ids.ubl_cii_tax_category_code == tax_unece_code
            and invoice_line.tax_ids.ubl_cii_tax_exemption_reason_code
            == tax_exemption_reason_code
        ):
            # stop if the result already matches the UNECE code
            return res
        taxes = self._get_tax_by_ubl_values(
            journal,
            amount,
            tax_unece_code,
            tax_exemption_reason_code=tax_exemption_reason_code,
            invoice_line=invoice_line,
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
