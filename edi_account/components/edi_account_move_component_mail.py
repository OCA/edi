# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EdiAccountMoveMail(Component):
    _name = "edi.account.move.mail"
    _inherit = "edi.format.connector.mail"
    _apply_on = "account.move"
