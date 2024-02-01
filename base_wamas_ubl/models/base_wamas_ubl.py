# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models

from ..lib.wamas.structure import MappingDict
from ..lib.wamas.ubl2wamas import ubl2wamas
from ..lib.wamas.utils import (
    detect_wamas_type,
    dict2wamas,
    get_supported_telegram,
    get_supported_telegram_w2w,
)
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
        extra_data = self._build_unitcode_mapping()
        return dict2ubl(template, data, extra_data=extra_data)

    @api.model
    def wamas2ubl(self, str_file, extra_data=False):
        extra_data = extra_data if extra_data else {}
        extra_data.update(self._build_unitcode_mapping())
        return wamas2ubl(str_file, extra_data=extra_data)

    @api.model
    def ubl2wamas(self, str_file, telegram_type):
        extra_data = self._build_unitcode_mapping()
        return ubl2wamas(str_file, telegram_type, extra_data=extra_data)

    @api.model
    def dict2wamas(self, dict_input, telegram_type):
        extra_data = self._build_unitcode_mapping()
        return dict2wamas(dict_input, telegram_type, extra_data=extra_data)

    @api.model
    def get_wamas_type(self, str_file):
        data, lst_telegram_type, wamas_type = detect_wamas_type(str_file)
        return data, lst_telegram_type, wamas_type

    @api.model
    def wamas2wamas(self, str_file):
        return wamas2wamas(str_file)

    @api.model
    def record_data_to_wamas(self, data, telegram_type):
        """
        Convert Odoo record data to WAMAS format

        :return: data as WAMAS format
        :rtype: bytes
        """
        if not telegram_type:
            raise ValueError(_("Please define telegram_type."))
        if not isinstance(data, dict):
            raise ValueError(_("The data is not valid."))
        return self.dict2wamas(data, telegram_type)

    @api.model
    def get_supported_telegram(self):
        return get_supported_telegram()

    @api.model
    def get_supported_telegram_w2w(self):
        return get_supported_telegram_w2w()

    @api.model
    def _build_unitcode_mapping(self):
        uom_records = self.env["uom.uom"].search([])
        uom_records = uom_records.filtered(
            lambda rec: rec.wamas_code and rec.unece_code
        )
        if not uom_records:
            return {}

        MAPPING_UNITCODE_WAMAS_TO_UBL = {
            "unitCode": MappingDict(
                {
                    "": False,  # undefined,
                }
            )
        }
        MAPPING_UNITCODE_UBL_TO_WAMAS = {"unitCode": MappingDict()}
        for uom_record in uom_records:
            MAPPING_UNITCODE_WAMAS_TO_UBL["unitCode"][
                uom_record.wamas_code
            ] = uom_record.unece_code
            MAPPING_UNITCODE_UBL_TO_WAMAS["unitCode"][
                uom_record.unece_code
            ] = uom_record.wamas_code
        return {
            "MAPPING_UNITCODE_WAMAS_TO_UBL": MAPPING_UNITCODE_WAMAS_TO_UBL,
            "MAPPING_UNITCODE_UBL_TO_WAMAS": MAPPING_UNITCODE_UBL_TO_WAMAS,
        }
