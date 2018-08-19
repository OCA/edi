# -*- coding: utf-8 -*-
# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class WeboobModuleUpdate(models.TransientModel):
    _name = 'weboob.module.update'
    _description = 'Update Weboob module list'

    def run(self):
        self.ensure_one()
        self.env['weboob.module'].update_module_list()
        action = self.env['ir.actions.act_window'].for_xml_id(
            'account_invoice_download_weboob', 'weboob_module_action')
        return action
