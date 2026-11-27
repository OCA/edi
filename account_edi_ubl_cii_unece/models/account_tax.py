# Copyright 2026 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = "account.tax"

    unece_type_code = fields.Selection(
        # Codes from UNTDID 5153
        # https://service.unece.org/trade/untdid/d24a/tred/tred5153.htm
        [
            ("VAT", "VAT - Value Added Tax"),  # MOST used by far - First position
            ("AAA", "AAA - Petroleum tax"),
            ("AAB", "AAB - Provisional countervailing duty cash"),
            ("AAC", "AAC - Provisional countervailing duty bond"),
            ("AAD", "AAD - Tobacco tax"),
            ("AAE", "AAE - Energy fee"),
            ("AAF", "AAF - Coffee tax"),
            ("AAG", "AAG - Harmonised sales tax, Canadian"),
            ("AAH", "AAH - Quebec sales tax"),
            ("AAI", "AAI - Canadian provincial sales tax"),
            ("AAJ", "AAJ - Tax on replacement part"),
            ("AAK", "AAK - Mineral oil tax"),
            ("AAL", "AAL - Special tax"),
            ("AAM", "AAM - Insurance tax"),
            ("AAO", "AAO - Provincial Cannabis Tax"),
            ("AAP", "AAP - Outstanding duty interest"),
            ("ADD", "ADD - Anti-dumping duty"),
            ("BOL", "BOL - Stamp duty (Imposta di Bollo)"),
            ("CAP", "CAP - Agricultural levy"),
            ("CAR", "CAR - Car tax"),
            ("COC", "COC - Paper consortium tax (Italy)"),
            ("CST", "CST - Commodity specific tax"),
            ("CUD", "CUD - Customs duty"),
            ("CVD", "CVD - Countervailing duty"),
            ("ENV", "ENV - Environmental tax"),
            ("EXC", "EXC - Excise duty"),
            ("EXP", "EXP - Agricultural export rebate"),
            ("FET", "FET - Federal excise tax"),
            ("FRE", "FRE - Free"),
            ("GCN", "GCN - General construction tax"),
            ("GST", "GST - Goods and services tax"),
            ("ILL", "ILL - Illuminants tax"),
            ("IMP", "IMP - Import tax"),
            ("IND", "IND - Individual tax"),
            ("LAC", "LAC - Business license fee"),
            ("LCN", "LCN - Local construction tax"),
            ("LDP", "LDP - Light dues payable"),
            ("LOC", "LOC - Local sales tax"),
            ("LST", "LST - Lust tax"),
            ("MCA", "MCA - Monetary compensatory amount"),
            ("MCD", "MCD - Miscellaneous cash deposit"),
            ("OTH", "OTH - Other taxes"),
            ("PDB", "PDB - Provisional duty bond"),
            ("PDC", "PDC - Provisional duty cash"),
            ("PRF", "PRF - Preference duty"),
            ("SCN", "SCN - Special construction tax"),
            ("SSS", "SSS - Shifted social securities"),
            ("STT", "STT - State/provincial sales tax"),
            ("SUP", "SUP - Suspended duty"),
            ("SUR", "SUR - Surtax"),
            ("SWT", "SWT - Shifted wage tax"),
            ("TAC", "TAC - Alcohol mark tax"),
            ("TOT", "TOT - Total"),
            ("TOX", "TOX - Turnover tax"),
            ("TTA", "TTA - Tonnage taxes"),
            ("VAD", "VAD - Valuation deposit"),
        ],
        compute="_compute_unece_code",
        store=True,
        readonly=False,
        string="UNECE Type",
    )
    # native field: we convert it to computed field
    ubl_cii_tax_category_code = fields.Selection(
        compute="_compute_ubl_cii_tax_category_code", store=True, readonly=False
    )

    @api.depends("amount_type")
    def _compute_unece_code(self):
        for tax in self:
            if tax.amount_type == "percent":
                tax.unece_type_code = "VAT"
            else:
                tax.unece_type_code = "OTH"

    @api.depends("unece_type_code")
    def _compute_ubl_cii_tax_category_code(self):
        for tax in self:
            if tax.unece_type_code != "VAT":
                tax.ubl_cii_tax_category_code = False

    @api.constrains(
        "type_tax_use",
        "active",
        "unece_type_code",
        "amount_type",
        "ubl_cii_tax_category_code",
        "ubl_cii_tax_exemption_reason_code",
        "ubl_cii_tax_exemption_reason",
    )
    def _check_unece_config(self):
        for tax in self:
            if tax.unece_type_code == "VAT":
                if tax.amount_type != "percent":
                    raise ValidationError(
                        self.env._(
                            "Tax '%s' has UNECE Type 'VAT' so its "
                            "Tax Computation should be 'Percentage'.",
                            tax.display_name,
                        )
                    )
                if tax.type_tax_use == "sale" and tax.active:
                    if not tax.ubl_cii_tax_category_code:
                        raise ValidationError(
                            self.env._(
                                "On sale VAT tax '%s' you must set a "
                                "Tax Category Code.",
                                tax.display_name,
                            )
                        )
                    if (
                        tax.ubl_cii_requires_exemption_reason
                        and not tax.ubl_cii_tax_exemption_reason_code
                        and not tax.ubl_cii_tax_exemption_reason
                    ):
                        raise ValidationError(
                            self.env._(
                                "On sale VAT tax '%(tax)s' that has Tax Category Code "
                                "'%(unece_categ)s', you must set a "
                                "Tax Exemption Reason Code or a Tax Exemption Reason.",
                                tax=tax.display_name,
                                unece_categ=dict(
                                    self._fields[
                                        "ubl_cii_tax_category_code"
                                    ]._description_selection(self.env)
                                ).get(tax.ubl_cii_tax_category_code),
                            )
                        )

    @api.model
    def _get_unece_code_from_tax_exigibility(self, tax_exigibility):
        mapping = {
            "on_invoice": "5",
            "on_payment": "72",
        }
        return mapping.get(tax_exigibility)

    @api.model
    def _get_tax_exigibility_from_unece_code(self, unece_code):
        if isinstance(unece_code, int):
            unece_code = str(unece_code)
        mapping = {
            "5": "on_invoice",
            "29": "on_invoice",
            "72": "on_payment",
        }
        if unece_code in mapping:
            return mapping[unece_code]
        else:
            return None

    def _get_unece_due_date_type_code(self):
        self.ensure_one()
        if self.tax_exigibility:
            return self._get_unece_code_from_tax_exigibility(self.tax_exigibility)
        else:
            return None
