# -*- coding: utf-8 -*-
# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def initial_update_module_list(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        try:
            env['weboob.module'].update_module_list()
        except Exception:
            pass
    return
