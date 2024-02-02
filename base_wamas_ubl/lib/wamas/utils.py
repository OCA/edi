import ast
import codecs
import logging
import os
import re
import struct
from collections import OrderedDict
from datetime import date, datetime, timedelta
from pprint import pprint
from random import randint, randrange

import pytz
from dateutil.parser import parse

_logger = logging.getLogger("wamas_utils")

# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from . import miniqweb
    from .const import (
        DEFAULT_TIMEZONE,
        DICT_CHILD_KEY,
        DICT_CONVERT_WAMAS_TYPE,
        DICT_DETECT_WAMAS_TYPE,
        DICT_PARENT_KEY,
        DICT_WAMAS_GRAMMAR,
        LST_FIELD_UNIT_CODE,
        LST_TELEGRAM_TYPE_IGNORE_W2D,
        LST_TELEGRAM_TYPE_SUPPORT_D2W,
        LST_TELEGRAM_TYPE_SUPPORT_W2D,
        MAPPING_UNITCODE_UBL_TO_WAMAS,
        MAPPING_UNITCODE_WAMAS_TO_UBL,
        SYSTEM_ERP,
        SYSTEM_WAMAS,
        TELEGRAM_HEADER_GRAMMAR,
    )
    from .structure import obj
except ImportError:
    import miniqweb
    from const import (
        DEFAULT_TIMEZONE,
        DICT_CHILD_KEY,
        DICT_CONVERT_WAMAS_TYPE,
        DICT_DETECT_WAMAS_TYPE,
        DICT_PARENT_KEY,
        DICT_WAMAS_GRAMMAR,
        LST_FIELD_UNIT_CODE,
        LST_TELEGRAM_TYPE_IGNORE_W2D,
        LST_TELEGRAM_TYPE_SUPPORT_D2W,
        LST_TELEGRAM_TYPE_SUPPORT_W2D,
        MAPPING_UNITCODE_UBL_TO_WAMAS,
        MAPPING_UNITCODE_WAMAS_TO_UBL,
        SYSTEM_ERP,
        SYSTEM_WAMAS,
        TELEGRAM_HEADER_GRAMMAR,
    )
    from structure import obj


def file_path(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)


def file_open(path):
    return codecs.open(path, "r", "iso-8859-1")


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
    res = str(float(val or 0))

    # Check if it is int / float or not
    if not res.replace(".", "", 1).isdigit():
        raise Exception(
            "The value '%s' is not the float type. Please check it again!" % res
        )

    str_whole_number, str_decimal_portion = res.split(".")
    str_whole_number = str_whole_number.rjust(length - dp, "0")
    str_decimal_portion = str_decimal_portion.ljust(dp, "0")

    return (str_whole_number + str_decimal_portion)[:length]


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


def convert_unit_code(key, val):
    if key in LST_FIELD_UNIT_CODE:
        return MAPPING_UNITCODE_UBL_TO_WAMAS["unitCode"].get(val, val)
    return val


def get_address_elements(dict_item):
    return {
        "ContactName": dict_item.get(
            "DespatchAdvice.cac:DeliveryCustomerParty.cac:Party.cac:Contact.cbc:Name"
        ),
        "PartyName": dict_item.get(
            "DespatchAdvice.cac:DeliveryCustomerParty."
            "cac:Party.cac:PartyName.cbc:Name"
        ),
        "Department": dict_item.get(
            "DespatchAdvice.cac:DeliveryCustomerParty."
            "cac:Party.cac:PostalAddress.cbc:Department"
        ),
        "StreetName": dict_item.get(
            "DespatchAdvice.cac:DeliveryCustomerParty."
            "cac:Party.cac:PostalAddress.cbc:StreetName"
        ),
        "AdditionalStreetName": dict_item.get(
            "DespatchAdvice.cac:DeliveryCustomerParty."
            "cac:Party.cac:PostalAddress.cbc:AdditionalStreetName"
        ),
    }


def get_Adrs_Name(a):
    return a["ContactName"] or a["PartyName"]


def get_Adrs_Name2(a):
    return next(filter(None, [a["PartyName"], a["Department"], a["StreetName"]]), "")


def get_Adrs_Name3(a):
    return next(filter(None, [a["Department"], a["StreetName"]]), "")


def get_Adrs_Name4(a):
    return a["StreetName"]


def get_Adrs_Adr(a):
    return a["AdditionalStreetName"] or a["StreetName"]


def generate_wamas_line(dict_item, grammar, **kwargs):  # noqa: C901
    res = ""
    dict_parent_id = kwargs.get("dict_parent_id", {})
    telegram_type_out = kwargs.get("telegram_type_out", False)
    dict_wamas_out = {}
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
            elif df_func == "get_random_str_num":
                args = (length,)
            elif "get_date_from_field" in df_func:
                args = (dict_wamas_out,)
                args += ast.literal_eval(re.search(r"\((.*?)\)", df_func).group(0))
                df_func = "get_date_from_field"
            # TODO: Consider refactoring to use classes
            # or provide a better way to determine arguments.
            elif "get_Adrs_" in df_func:
                address_elements = get_address_elements(dict_item)
                args = (address_elements,)

            val = globals()[df_func](*args)

        val = convert_unit_code(_key, val)
        if kwargs.get("check_to_set_value_to_string", False):
            # Ignore convert string of float/int/date/datetime type
            # to move entire value when convert wamas2wamas
            if (
                not val
                or _key in ["Telheader_TelSeq", "Telheader_AnlZeit"]
                or df_func
                or ttype not in ["float", "int", "date", "datetime"]
            ):
                val = set_value_to_string(
                    val, ttype, length, dp, do_convert_tz=do_convert_tz
                )
        else:
            val = set_value_to_string(
                val, ttype, length, dp, do_convert_tz=do_convert_tz
            )
        dict_wamas_out[_key] = val
        res += val
        lst_parent_key = DICT_PARENT_KEY.get(telegram_type_out, False)
        if lst_parent_key and _key in lst_parent_key:
            dict_parent_id[_key] = val
    return res


def generate_wamas_lines(dict_input, telegram_type, line_idx, wamas_lines):
    line_idx += 1
    grammar = DICT_WAMAS_GRAMMAR[telegram_type.lower()]
    line = generate_wamas_line(dict_input, grammar, line_idx=line_idx)
    if line:
        wamas_lines.append(line)
    return line_idx, wamas_lines


def dict2wamas(dict_input, telegram_type):
    wamas_lines = []
    lst_telegram_type = telegram_type.split(",")

    if not all(x in LST_TELEGRAM_TYPE_SUPPORT_D2W for x in lst_telegram_type):
        raise Exception("Invalid telegram types: %s" % telegram_type)

    line_idx = 0
    for telegram_type in lst_telegram_type:
        # Special case for `KSTAUS`
        if telegram_type == "KSTAUS":
            # 1 line for `KstAus_LagIdKom = kMEZ`
            dict_input["picking_zone"] = "kMEZ"
            line_idx, wamas_lines = generate_wamas_lines(
                dict_input, telegram_type, line_idx, wamas_lines
            )
            # 1 line for `KstAus_LagIdKom = kPAR`
            dict_input["picking_zone"] = "kPAR"
            line_idx, wamas_lines = generate_wamas_lines(
                dict_input, telegram_type, line_idx, wamas_lines
            )
        else:
            line_idx, wamas_lines = generate_wamas_lines(
                dict_input, telegram_type, line_idx, wamas_lines
            )
    return "\n".join(wamas_lines).encode("iso-8859-1")


def _get_grammar(telegram_type, use_simple_grammar=False):
    if use_simple_grammar:
        grammar = DICT_WAMAS_GRAMMAR[telegram_type.lower()]
        if not isinstance(list(grammar.values())[0], dict):
            return grammar
        simple_grammar = OrderedDict()
        for field in grammar:
            if field in TELEGRAM_HEADER_GRAMMAR.keys():
                continue
            simple_grammar[field] = grammar[field]["length"]
        return simple_grammar
    return DICT_WAMAS_GRAMMAR[telegram_type.lower()]


def fw2dict(line, grammar, telegram_type, verbose=False):
    """
    Convert a fixed width to a dict

    definition: { "k1": 3, "k2": 5 }
    line: abcdefgh
    """

    # prepare format
    fieldwidths = grammar.values()
    fmtstring = " ".join("{}{}".format(abs(fw), "s") for fw in fieldwidths)
    unpack = struct.Struct(fmtstring).unpack_from

    # sanity checks
    expected_size = sum(fieldwidths)
    line = line.encode("iso-8859-1")
    if len(line) != expected_size:
        _logger.debug(
            "Line of length %d does not match expected length %d: %s",
            len(line),
            expected_size,
            line.decode("iso-8859-1"),
        )
        _logger.debug(repr(unpack(line)))

        if abs(len(line) - expected_size) == 1 and telegram_type in (
            "WATEKQ",
            "WATEPQ",
        ):
            _logger.debug("Length off by one only, fields not impacted, no fix needed.")

        elif telegram_type == "WATEPQ":
            # line_WATEPQ_-_weirdly_encoded_01.wamas
            # - this case has a weird WATEPQ:IvTep_MId_Charge
            #   of incorrect size due to weirdly encoded chars inside:
            #   b'6423033A\xc3\xa9\xc2\xb0\xc2\xb0\xc3\xaf\xc2\xbf\xc2\xbd
            #   \xc3\xaf\xc2\xbf\xc2\xbd370063 '
            #   33 chars instead of expected 20 (when file is decoded as iso-8859-1)
            # - we clean it from non ascii chars and fill it with space to fix length
            #   and avoid impact on other fields
            to_fix = line.split(b" ")[0]
            to_keep_idx = len(to_fix) + 1
            line = (
                to_fix.decode("iso-8859-1").encode("ascii", "ignore").ljust(20, b" ")
                + line[to_keep_idx:]
            )

            if len(line) is expected_size:
                _logger.debug("Line corrected successfully.")
            else:
                _logger.debug(
                    "Line of length %d still does not match expected length %d: %s",
                    len(line),
                    expected_size,
                    line.decode("iso-8859-1"),
                )

    # actual parsing
    try:
        vals = tuple(s.decode("iso-8859-1") for s in unpack(line))
    except struct.error as e:
        _logger.debug(line)
        raise e

    # cleaning
    vals = [v.strip() for v in vals]
    vals_with_keys = list(zip(grammar.keys(), vals))
    vals_with_lengths = list(zip(vals_with_keys, fieldwidths, list(map(len, vals))))
    if verbose:
        pprint(vals_with_lengths)
    res = dict(vals_with_keys)
    return res


def wamas2dict(
    infile, lst_valid_telgram=False, use_simple_grammar=False, verbose=False
):
    header_len = sum(TELEGRAM_HEADER_GRAMMAR.values())
    result = {}
    lst_telegram_type_in = []

    if not lst_valid_telgram:
        lst_valid_telgram = LST_TELEGRAM_TYPE_SUPPORT_W2D

    for line in infile.splitlines():
        if not line:
            continue
        head = fw2dict(line[:header_len], TELEGRAM_HEADER_GRAMMAR, "header")
        telegram_type, telegram_seq, dummy = re.split(r"(\d+)", head["Satzart"], 1)
        # ignore useless telegram types
        if telegram_type in LST_TELEGRAM_TYPE_IGNORE_W2D:
            continue
        if telegram_type not in lst_valid_telgram:
            raise Exception("Invalid telegram type: %s" % telegram_type)
        lst_telegram_type_in.append(telegram_type)
        grammar = _get_grammar(telegram_type, use_simple_grammar)
        body = fw2dict(line[header_len:], grammar, telegram_type)
        val = result.setdefault(telegram_type, [])
        val.append(body)
    lst_telegram_type_in = list(set(lst_telegram_type_in))
    if verbose:
        pprint(result)
    return result, lst_telegram_type_in


def dict2ubl(template, data, verbose=False, extra_data=False):
    t = miniqweb.QWebXml(template)
    # Convert dict to object to use dotted notation in template
    globals_dict = {
        "record": obj(data),
        "get_date": get_date,
        "get_time": get_time,
        "get_current_date": get_current_date,
        "MAPPING": MAPPING_UNITCODE_WAMAS_TO_UBL,
        "extra_data": extra_data,
    }
    xml = t.render(globals_dict)
    if verbose:
        pprint(xml)
    return xml


def detect_wamas_type(infile):
    data, lst_telegram_type = wamas2dict(infile, use_simple_grammar=True)
    lst_telegram_type.sort()
    wamas_type = DICT_DETECT_WAMAS_TYPE.get(tuple(lst_telegram_type), "Undefined")
    return data, lst_telegram_type, wamas_type


def convert_tz(dt_val, str_from_tz, str_to_tz):
    from_tz = pytz.timezone(str_from_tz)
    to_tz = pytz.timezone(str_to_tz)
    from_tz_dt = from_tz.localize(dt_val)
    to_tz_dt = from_tz_dt.astimezone(to_tz)
    return to_tz_dt


def get_supported_telegram():
    return LST_TELEGRAM_TYPE_SUPPORT_W2D


def get_supported_telegram_w2w():
    return DICT_CONVERT_WAMAS_TYPE
