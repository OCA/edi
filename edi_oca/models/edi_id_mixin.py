# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EDIIdMixin(models.AbstractModel):
    """Mixin to expose identifier's features"""

    _name = "edi.id.mixin"
    _description = "EDI ID mixin"

    edi_id = fields.Char(help="Internal or external identifier for records.")
