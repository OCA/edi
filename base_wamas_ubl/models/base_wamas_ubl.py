# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models

from ..lib.wamas.ubl2wamas import ubl2wamas
from ..lib.wamas.utils import detect_wamas_type, dict2wamas
from ..lib.wamas.wamas2ubl import dict2ubl, wamas2dict, wamas2ubl
from ..lib.wamas.wamas2wamas import wamas2wamas


class BaseWamasUbl(models.AbstractModel):
    _name = "base.wamas.ubl"
    _description = "Methods to convert WAMAS to UBL XML files and vice versa"

    @api.model
    def wamas2dict(self, str_file):
        return wamas2dict(str_file)

    @api.model
    def dict2ubl(self, template, data):
        return dict2ubl(template, data)

    @api.model
    def wamas2ubl(self, str_file, extra_data=False):
        return wamas2ubl(str_file, extra_data=extra_data)

    @api.model
    def ubl2wamas(self, str_file, telegram_type):
        return ubl2wamas(str_file, telegram_type)

    @api.model
    def dict2wamas(self, dict_input, telegram_type):
        return dict2wamas(dict_input, telegram_type)

    @api.model
    def get_wamas_type(self, str_file):
        data, lst_telegram_type, wamas_type = detect_wamas_type(str_file)
        return data, lst_telegram_type, wamas_type

    @api.model
    def wamas2wamas(self, str_file):
        return wamas2wamas(str_file)
