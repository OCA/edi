# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    voxel_tax_code = fields.Selection(
        selection=[
            ("IVA", "(IVA) IVA"),
            ("IGIC", "(IGIC) IGIC"),
            ("IRPF", "(IRPF) IRPF"),
            ("RE", "(RE) Recargo de equivalencia"),
            (
                "ITPAJD",
                "(ITPAJD) Impuesto sobre transmisiones patrimoniales y "
                "actos jurídicos documentados",
            ),
            ("IE", "(IE) Impuestos especiales"),
            ("RA", "(RA) Renta aduanas"),
            (
                "IGTECM",
                "(IGTECM) Impuesto general sobre el tráfico de "
                "empresas que se aplica en Ceuta y Melilla",
            ),
            (
                "IECDPCAC",
                "(IECDPCAC) Impuesto especial sobre los combustibles "
                "derivados del petróleo en la comunidad Autónoma "
                "Canaria",
            ),
            (
                "IIIMAB",
                "(IIIMAB) Impuesto sobre las instalaciones que inciden "
                "sobre le medio ambiente en las Baleares",
            ),
            (
                "ICIO",
                "(ICIO) Impuesto sobre las construcciones, instalaciones " "y obras",
            ),
            (
                "IMVDN",
                "(IMVDN) Impuesto municipal sobre las viviendas "
                "desocupadas en Navarra",
            ),
            ("IMSN", "(IMSN) Impuesto municipal sobre solares en Navarra"),
            (
                "IMGSN",
                "(IMGSN) Impuesto municipal sobre gastos " "suntuarios en Navarra",
            ),
            ("IMPN", "(IMPN) Impuesto municipal sobre publicidad en Navarra"),
            ("IBA", "(IBA) Impuesto sobre bebidas alcohólicas"),
            ("IHC", "(IHC) Impuesto sobre harinas cárnicas"),
            ("EXENTO", "(EXENTO) Exento"),
            ("OTRO", "(OTRO) Otro"),
        ],
    )
