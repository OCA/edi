# Copyright 2017-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BaseFacturX(models.AbstractModel):
    _name = "base.facturx"
    _description = "Common methods to generate and parse Factur-X invoices"
