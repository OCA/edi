# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models

from ..lib.wamas.dict2wamas import dict2wamas
from ..lib.wamas.ubl2wamas import ubl2wamas
from ..lib.wamas.utils import (
    detect_wamas_type,
    get_supported_telegram,
    get_supported_telegram_w2w,
)
from ..lib.wamas.wamas2ubl import dict2ubl, wamas2dict, wamas2ubl
from ..lib.wamas.wamas2wamas import wamas2wamas


class BaseWamasUbl(models.AbstractModel):
    _name = "base.wamas.ubl"
    _description = "Methods to convert WAMAS to UBL XML files and vice versa"

    @api.model
    def wamas2dict(self, wamas_msg):
        return wamas2dict(wamas_msg)

    @api.model
    def dict2ubl(self, msg_type, data, extra_data=False):
        return dict2ubl(msg_type, data, extra_data=extra_data)

    @api.model
    def wamas2ubl(self, wamas_msg, extra_data=False):
        return wamas2ubl(wamas_msg, extra_data=extra_data)

    @api.model
    def ubl2wamas(self, str_file, msg_type):
        return ubl2wamas(str_file, msg_type)

    @api.model
    def dict2wamas(self, dict_input, msg_type):
        return dict2wamas(dict_input, msg_type)

    @api.model
    def get_wamas_type(self, str_file):
        return detect_wamas_type(str_file)

    @api.model
    def wamas2wamas(self, str_file):
        return wamas2wamas(str_file)

    @api.model
    def record_data_to_wamas(self, data, msg_type):
        """
        Convert Odoo record data to WAMAS format

        :return: data as WAMAS format
        :rtype: bytes
        """
        if not msg_type:
            raise ValueError(_("Please define wamas message type (msg_type)."))
        if not isinstance(data, dict):
            raise ValueError(_("The data is not valid."))
        return self.dict2wamas(data, msg_type)

    @api.model
    def get_supported_telegram(self):
        return get_supported_telegram()

    @api.model
    def get_supported_telegram_w2w(self):
        return get_supported_telegram_w2w()
