# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WamasDocumentDefaultField(models.Model):
    _name = "wamas.document.default.field"
    _inherit = "wamas.document.field"
    _description = "WAMAS Document Default Field"
