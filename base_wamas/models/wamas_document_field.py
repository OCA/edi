# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from dateutil.parser import parse

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

FIELD_TYPES = [
    ("str", "String"),
    ("int", "Integer"),
    ("float", "Float"),
    ("date", "Date"),
    ("datetime", "Datetime"),
    ("bool", "Boolean"),
]


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


class WamasDocumentField(models.Model):
    _name = "wamas.document.field"
    _description = "WAMAS Document Field"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    ttype = fields.Selection(FIELD_TYPES, "Type", required=True)
    len_field = fields.Integer("Length", required=True)
    decimal_place = fields.Integer()
    sequence = fields.Integer(required=True, default=10)
    element_id = fields.Many2one("wamas.document.element", "Element")

    def get_value_from_string(self, value):
        self.ensure_one()

        res = value

        if self.ttype == "str":
            res = self._get_string(value)
        elif self.ttype == "int":
            res = self._get_int(value)
        elif self.ttype == "float":
            res = self._get_float(value)
        elif self.ttype == "date":
            res = self._get_date(value)
        elif self.ttype == "datetime":
            res = self._get_datetime(value)
        elif self.ttype == "bool":
            res = self._get_bool(value)

        return res

    def set_value_to_string(self, value):
        self.ensure_one()

        res = value

        if self.ttype == "str":
            res = self._set_from_string(value)
        elif self.ttype == "int":
            res = self._set_from_int(value)
        elif self.ttype == "float":
            res = self._set_from_float(value)
        elif self.ttype == "date":
            res = self._set_from_date(value)
        elif self.ttype == "datetime":
            res = self._set_from_datetime(value)
        elif self.ttype == "bool":
            res = self._set_from_bool(value)

        return res

    def _get_string(self, value):
        self.ensure_one()

        res = value.strip()

        return res

    def _get_int(self, value):
        self.ensure_one()

        res = value.strip()

        try:
            res = int(res)
        except TypeError:  # pylint: disable=except-pass
            pass

        return res

    def _get_float(self, value):
        self.ensure_one()

        res = value.strip()

        try:
            if len(res) >= self.len_field:
                str_whole_number = res[: self.len_field - self.decimal_place]
                str_decimal_portion = res[self.decimal_place * -1 :]

                res = str_whole_number + "." + str_decimal_portion

                res = float(res.strip())
        except TypeError:  # pylint: disable=except-pass
            pass

        return res

    def _get_date(self, value):
        self.ensure_one()

        res = value.strip()

        try:
            if res:
                res = parse(res).date()
        except TypeError:  # pylint: disable=except-pass
            pass

        return res

    def _get_datetime(self, value):
        self.ensure_one()

        res = value.strip()

        try:
            if res:
                res = parse(res)
        except TypeError:  # pylint: disable=except-pass
            pass

        return res

    def _get_bool(self, value):
        self.ensure_one()

        res = value.strip()

        ICP = self.env["ir.config_parameter"]
        lst_false = safe_eval(ICP.get_param("wamas_document_list_false_value", ["f"]))
        lst_true = safe_eval(ICP.get_param("wamas_document_list_true_value", ["t"]))

        try:
            if value.lower() in lst_false:
                res = False
            elif value.lower() in lst_true:
                res = True
        except TypeError:  # pylint: disable=except-pass
            pass

        return res

    def _set_from_string(self, value):
        self.ensure_one()

        res = str(value).ljust(self.len_field)[: self.len_field]

        return res

    def _set_from_int(self, value):
        self.ensure_one()

        res = str(value).rjust(self.len_field, "0")[: self.len_field]

        return res

    def _set_from_float(self, value):
        self.ensure_one()

        res = str(float(value))

        # Check if it is int / float or not
        if not res.replace(".", "", 1).isdigit():
            raise UserError(
                _(
                    "The value '%s' is not the float type. "
                    "Please check it again!" % res
                )
            )

        str_whole_number, str_decimal_portion = res.split(".")

        str_whole_number = str_whole_number.rjust(
            self.len_field - self.decimal_place, "0"
        )
        str_decimal_portion = str_decimal_portion.ljust(self.decimal_place, "0")

        res = (str_whole_number + str_decimal_portion)[: self.len_field]

        return res

    def _set_from_date(self, value):
        self.ensure_one()

        res = value

        if isinstance(res, date):
            res = res.strftime("%Y%m%d")
        elif isinstance(res, datetime):
            res = res.date().strftime("%Y%m%d")
        elif isinstance(res, str):
            if res == "":
                res = res.ljust(self.len_field)
            elif not is_date(res):
                raise UserError(
                    _(
                        "The value '%s' is not the date type. "
                        "Please check it again!" % value
                    )
                )
        else:
            res = str(value).ljust(self.len_field)

        res = res[: self.len_field]

        return res

    def _set_from_datetime(self, value):
        self.ensure_one()

        res = value

        if isinstance(res, (date, datetime)):
            res = res.strftime("%Y%m%d%H%M%S")
        elif isinstance(res, str):
            if res == "":
                res = res.ljust(self.len_field)
            elif not is_date(res):
                raise UserError(
                    _(
                        "The value '%s' is not the datetime type. "
                        "Please check it again!" % value
                    )
                )
        else:
            res = str(value).ljust(self.len_field)

        res = res[: self.len_field]

        return res

    def _set_from_bool(self, value):
        self.ensure_one()

        ICP = self.env["ir.config_parameter"]
        default_false_value = safe_eval(
            ICP.get_param("wamas_document_default_false_value", "F")
        )
        default_true_value = safe_eval(
            ICP.get_param("wamas_document_default_true_value", "T")
        )

        res = default_false_value

        if value:
            res = default_true_value

        res = res[: self.len_field]

        return res
