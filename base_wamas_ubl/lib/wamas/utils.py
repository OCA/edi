# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import ast
import logging
import os
import re
from collections import OrderedDict
from datetime import date, datetime, timedelta
from pprint import pformat
from random import randint, randrange

import pytz
from dateutil.parser import parse
from markupsafe import escape

from .const import (
    DEFAULT_TIMEZONE,
    DICT_CHILD_KEY,
    DICT_CONVERT_WAMAS_TYPE,
    DICT_DETECT_WAMAS_TYPE,
    DICT_PARENT_KEY,
    DICT_WAMAS_GRAMMAR,
    SYSTEM_ERP,
    SYSTEM_WAMAS,
)

_logger = logging.getLogger("wamas_utils")


def file_path(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)


def file_open(path, mode="r"):
    return open(path, mode, encoding="iso-8859-1")


def get_date(val):
    val = parse(val)
    if isinstance(val, datetime):
        val = convert_tz(val, DEFAULT_TIMEZONE, "UTC").strftime("%Y-%m-%d")
    return val


def get_time(val):
    val = parse(val)
    if isinstance(val, datetime):
        val = convert_tz(val, DEFAULT_TIMEZONE, "UTC").strftime("%H:%M:%S")
    return val


def get_current_date():
    # return convert_tz(datetime.utcnow(), DEFAULT_TIMEZONE, "UTC").strftime("%Y-%m-%d")
    return date.today()


def get_source(*args):
    return SYSTEM_ERP


def get_destination(*args):
    return SYSTEM_WAMAS


def get_source_q(*args):
    return SYSTEM_WAMAS


def get_destination_q(*args):
    return SYSTEM_ERP


def get_sequence_number(val=0):
    return val


def get_current_datetime(val=0):
    return datetime.utcnow()


def _set_string(val, length, dp, **kwargs):
    return str(val or "").ljust(length)[:length]


def _set_string_int(val, length, dp, **kwargs):
    if isinstance(val, float):
        val = int(val)
    return str(val).rjust(length, "0")[:length]


def _set_string_float(val, length, dp, **kwargs):
    try:
        res = str(float(val or 0))
    except ValueError as err:
        raise Exception(
            "The value '%s' is not the float type. Please check it again!" % res
        ) from err

    # Support for the negative float
    signed = ""
    if res.startswith("-"):
        signed = "-"
        length = length - 1
        res = res.lstrip("-")

    str_whole_number, str_decimal_portion = res.split(".")
    str_whole_number = str_whole_number.rjust(length - dp, "0")
    str_decimal_portion = str_decimal_portion.ljust(dp, "0")

    return signed + (str_whole_number + str_decimal_portion)[:length]


def _set_string_date(val, length, dp, **kwargs):
    res = isinstance(val, str) and val != "" and parse(val) or val

    if isinstance(res, date):
        res = res.strftime("%Y%m%d")
    elif isinstance(res, datetime):
        if kwargs.get("do_convert_tz", False):
            res = convert_tz(res, "UTC", DEFAULT_TIMEZONE)
        res = res.date().strftime("%Y%m%d")
    elif isinstance(res, str):
        res = res.ljust(length)
    elif not res:
        res = ""
    else:
        raise Exception(
            "The value '%s' is not the date type. Please check it again!" % res
        )

    return res[:length]


def _set_string_datetime(val, length, dp, **kwargs):
    res = isinstance(val, str) and val != "" and parse(val) or val

    if isinstance(res, (date, datetime)):
        if kwargs.get("do_convert_tz", False):
            res = convert_tz(res, "UTC", DEFAULT_TIMEZONE)
        res = res.strftime("%Y%m%d%H%M%S")
    elif isinstance(res, str):
        res = res.ljust(length)
    elif not res:
        res = ""
    else:
        raise Exception(
            "The value '%s' is not the date type. Please check it again!" % res
        )

    return res.ljust(length)[:length]


def _set_string_bool(val, length, dp, **kwargs):
    res = "N"
    if isinstance(val, str) and val:
        res = val[:length]
    elif isinstance(val, bool) and val:
        res = "J"
    return res


def set_value_to_string(val, ttype, length, dp, **kwargs):
    setters = dict(
        str=_set_string,
        int=_set_string_int,
        float=_set_string_float,
        date=_set_string_date,
        datetime=_set_string_datetime,
        bool=_set_string_bool,
    )
    return setters[ttype](val, length, dp, **kwargs)


def get_random_str_num(*args):
    range_start = 10 ** (args[0] - 1)
    range_end = (10 ** args[0]) - 1
    return str(randint(range_start, range_end))


def get_random_int_num(*args):
    return randrange(9999)


def get_parent_id(*args):
    dict_parent_id, dict_child_key, field, telegram_type_out = args
    return dict_parent_id[dict_child_key[telegram_type_out][field]]


def get_random_quai(*args):
    return "QUAI-%d" % randint(1, 999)


def get_date_from_field(*args):
    dict_wamas, field, number, interval = args
    res = parse(dict_wamas[field]) + timedelta(**{interval: number})
    return res


def get_address_elements(dict_item, party_type="DeliveryCustomerParty"):
    return {
        "ContactName": dict_item.get(
            f"DespatchAdvice.cac:{party_type}.cac:Party.cac:Contact.cbc:Name"
        ),
        "PartyName": dict_item.get(
            f"DespatchAdvice.cac:{party_type}.cac:Party.cac:PartyName.cbc:Name"
        ),
        "Department": dict_item.get(
            f"DespatchAdvice.cac:{party_type}.cac:Party.cac:PostalAddress.cbc:Department"
        ),
        "StreetName": dict_item.get(
            f"DespatchAdvice.cac:{party_type}.cac:Party.cac:PostalAddress.cbc:StreetName"
        ),
        "AdditionalStreetName": dict_item.get(
            f"DespatchAdvice.cac:{party_type}.cac:Party.cac:PostalAddress."
            "cbc:AdditionalStreetName"
        ),
    }


def _get_Name(a, index):
    candidates = (
        "ContactName",
        "PartyName",
        "Department",
        "StreetName",
        "AdditionalStreetName",
    )
    values = []
    for c in candidates:
        e = a.get(c)
        if e and e not in values:
            values.append(e)
    # always drop last element, that's the address
    values = values[index:-1]
    return values[0] if values else None


def get_Adrs_Name(a):
    return _get_Name(a, 0)


def get_Adrs_Name2(a):
    return _get_Name(a, 1)


def get_Adrs_Name3(a):
    return _get_Name(a, 2)


def get_Adrs_Name4(a):
    return _get_Name(a, 3)


def get_Adrs_Adr(a):
    return a["AdditionalStreetName"] or a["StreetName"] or a["Department"]


def get_index(idx):
    return idx


def wamas_dict2line(wamas_dict):
    """Converts a wamas OrderedDict to a telegram."""
    return "".join(wamas_dict.values())


def generate_wamas_line(dict_item, grammar, **kwargs):
    """Generate a wamas telegram."""
    wamas_dict = generate_wamas_dict(dict_item, grammar, **kwargs)
    return wamas_dict2line(wamas_dict)


def generate_wamas_dict(dict_item, grammar, **kwargs):  # noqa: C901
    """Generate an OrderedDict with wamas field and value."""
    dict_parent_id = kwargs.get("dict_parent_id", {})
    telegram_type_out = kwargs.get("telegram_type_out", False)
    dict_wamas_out = OrderedDict()
    do_convert_tz = not kwargs.get("do_wamas2wamas", False)
    for _key in grammar:
        val = ""
        ttype = grammar[_key].get("type", False)
        length = grammar[_key].get("length", False)
        dp = grammar[_key].get("dp", False)
        ubl_path = grammar[_key].get("ubl_path", False)
        dict_key = grammar[_key].get("dict_key", False)
        df_val = grammar[_key].get("df_val", False)
        df_func = grammar[_key].get("df_func", False)

        if ubl_path:
            # Get the `ubl_path` if it has multi lines
            len_loop = kwargs.get("len_loop", False)
            idx_loop = kwargs.get("idx_loop", False)
            if len_loop and len_loop > 1:
                ubl_path = "%s" in ubl_path and ubl_path % str(idx_loop) or ubl_path
            else:
                ubl_path = "%s" in ubl_path and ubl_path.replace(".%s", "") or ubl_path
            # Handle the type of `ubl_path`
            if isinstance(ubl_path, list):
                lst_val = []
                for _item in ubl_path:
                    lst_val.append(dict_item.get(_item, ""))
                if lst_val:
                    val = " ".join(lst_val)
            elif isinstance(ubl_path, dict):
                for _key in ubl_path:
                    if dict_item.get(_key, False):
                        val = dict_item.get(ubl_path[_key], "")
            elif isinstance(ubl_path, str):
                val = dict_item.get(ubl_path, "")
            else:
                val = ""
        if not val and dict_key:
            val = dict_item.get(dict_key, "")
        if not val and df_val:
            val = df_val
        if not val and df_func:
            args = (kwargs.get("line_idx", 0),)
            if df_func == "get_parent_id":
                args = (
                    dict_parent_id,
                    DICT_CHILD_KEY,
                    _key,
                    telegram_type_out,
                )
            elif df_func == "get_index":
                args = (kwargs.get("idx_loop", 0),)
            elif df_func == "get_random_str_num":
                args = (length,)
            elif "get_date_from_field" in df_func:
                args = (dict_wamas_out,)
                args += ast.literal_eval(re.search(r"\((.*?)\)", df_func).group(0))
                df_func = "get_date_from_field"
            # TODO: Consider refactoring to use classes
            # or provide a better way to determine arguments.
            elif "get_Adrs_" in df_func:
                if df_func.startswith("supplier"):
                    address_elements = get_address_elements(
                        dict_item, "DespatchSupplierParty"
                    )
                    df_func = df_func[9:]
                else:
                    address_elements = get_address_elements(dict_item)
                args = (address_elements,)

            val = globals()[df_func](*args)

        val = set_value_to_string(val, ttype, length, dp, do_convert_tz=do_convert_tz)
        dict_wamas_out[_key] = val
        lst_parent_key = DICT_PARENT_KEY.get(telegram_type_out, False)
        if lst_parent_key and _key in lst_parent_key:
            dict_parent_id[_key] = val
    return dict_wamas_out


def generate_wamas_lines(dict_input, telegram_type, line_idx, wamas_lines):
    line_idx += 1
    grammar = DICT_WAMAS_GRAMMAR[telegram_type]
    line = generate_wamas_line(dict_input, grammar, line_idx=line_idx)
    if line:
        wamas_lines.append(line)
    return line_idx, wamas_lines


def get_grammar(telegram_type):
    return DICT_WAMAS_GRAMMAR[telegram_type]


def fw2dict(line, grammar, telegram_type):
    """
    Converts a fixed width string to a dict

    Parameters:
        line (str): The string to convert
        grammar (OrderedDict): The field width definition in the format:
            { "k1": { "length": 3 }, "k2": { "length": 5 } }
        telegram_type (str): Telegram type

    Returns:
        OrderedDict: Same keys as the grammar, values from the string
    """
    # sanity checks
    max_length = min_length = sum(f["length"] for f in grammar.values())
    last_val = grammar[next(reversed(grammar))]
    if last_val["type"] == "str":
        min_length -= last_val["length"] + 1
    if not min_length <= len(line) <= max_length:
        raise Exception(
            "Line of length {actual:d} does not match expected length of "
            "{expected:d}:\n{line:s}".format(
                actual=len(line),
                expected=max_length,
                line=line,
            )
        )
    else:
        line = line.ljust(max_length)

    # actual parsing
    res = OrderedDict()
    offset = 0
    for fname, fdef in grammar.items():
        b = line[offset : offset + fdef["length"]]
        offset += fdef["length"]
        if fdef["type"] == "int":
            val = int(b)
        elif fdef["type"] == "float":
            dp = fdef["dp"]
            val = float(b[:-dp] + "." + b[-dp:])
        else:
            val = escape(b.rstrip())
        res[fname] = val
    _logger.debug(pformat(res))
    return res


def get_telegram_type(line):
    # given by Satzart at pos 49, len 9
    return re.split(r"(\d+)", line[40:49])[0]


def detect_wamas_type(infile):
    """
    Detect the type of message

    Parameters:
        line (str): The wamas message

    Returns:
        str: Type of message
    """
    wamas_type = DICT_DETECT_WAMAS_TYPE.get(get_telegram_type(infile), "Undefined")
    return wamas_type


def convert_tz(dt_val, str_from_tz, str_to_tz):
    from_tz = pytz.timezone(str_from_tz)
    to_tz = pytz.timezone(str_to_tz)
    from_tz_dt = from_tz.localize(dt_val)
    to_tz_dt = from_tz_dt.astimezone(to_tz)
    return to_tz_dt


def get_supported_telegram():
    return DICT_WAMAS_GRAMMAR.keys()


def get_supported_telegram_w2w():
    return DICT_CONVERT_WAMAS_TYPE
