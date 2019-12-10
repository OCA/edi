# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_payment_identifier(self):
        """This method is designed to be inherited in localization modules"""
        self.ensure_one()
        return None
