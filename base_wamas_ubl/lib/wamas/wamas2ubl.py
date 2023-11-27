#!/usr/bin/python3

import getopt
import logging
import sys
from pprint import pprint

_logger = logging.getLogger("wamas2ubl")

# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from .const import (
        DICT_FLOAT_FIELD,
        DICT_TUPLE_KEY_PICKING,
        DICT_TUPLE_KEY_RECEPTION,
    )
    from .utils import dict2ubl, file_open, file_path, wamas2dict
except ImportError:
    from const import DICT_FLOAT_FIELD, DICT_TUPLE_KEY_PICKING, DICT_TUPLE_KEY_RECEPTION
    from utils import dict2ubl, file_open, file_path, wamas2dict

##
# Data transformations
##


def _get_float(val, length=12, decimal_place=3):
    res = val.strip()

    try:
        if len(res) >= length:
            str_whole_number = res[: length - decimal_place]
            str_decimal_portion = res[decimal_place * -1 :]

            res = str_whole_number + "." + str_decimal_portion

            res = float(res.strip())
    except TypeError:
        _logger.debug("Cannot convert value '%s' to float type", val)

    return res


def _convert_float_field(data):
    for _field in DICT_FLOAT_FIELD:  # noqa: F405
        val_field = data.get(_field, False)
        if val_field:
            data[_field] = _get_float(
                val_field,
                DICT_FLOAT_FIELD[_field][0],
                DICT_FLOAT_FIELD[_field][1],
            )


def _prepare_receptions(data, order_name, order_key, line_name, line_key):
    orders = {}

    for order in data[order_name]:
        order_id = order[order_key]
        _convert_float_field(order)
        if order_id not in orders:
            order["lines"] = []
            orders[order_id] = order
        else:
            _logger.debug(
                "Redundant %s (order) record found, ignoring: %s", order_name, order_id
            )

    for line in data[line_name]:
        order_id = line[line_key]
        _convert_float_field(line)
        if order_id not in orders:
            _logger.debug(
                "Found %s (line) record for unknown %s (order), ignoring: %s",
                line_name,
                order_name,
                order_id,
            )
            continue
        orders[order_id]["lines"].append(line)

    return orders


def _prepare_pickings(data):
    pickings = {}
    packages = {}

    for order in data["AUSKQ"]:
        order_id = order["IvAusk_AusId_AusNr"]
        _convert_float_field(order)
        if order_id not in pickings:
            order["lines"] = []
            order["packages"] = set()
            pickings[order_id] = order
        else:
            _logger.debug(
                "Redundant AUSKQ (order) record found, ignoring: %s", order_id
            )

    for package in data["WATEKQ"]:
        package_id = package["IvTek_TeId"]
        _convert_float_field(package)
        if package_id not in packages:
            packages[package_id] = package
        else:
            _logger.debug(
                "Redundant WATEKQ (package) record found, ignoring: %s", package_id
            )

    for line in data["WATEPQ"]:
        order_id = line["IvAusp_UrAusId_AusNr"]
        _convert_float_field(line)
        if order_id not in pickings:
            _logger.debug(
                "Found WATEPQ (line) record for unknown AUSKQ (order), ignoring: %s",
                order_id,
            )
            continue
        pickings[order_id]["lines"].append(line)
        package_id = line["IvTep_TeId"]
        if package_id in packages:
            line["package"] = package
            pickings[order_id]["packages"].add(package_id)
        else:
            _logger.debug(
                "Found WATEPQ (line) record with unknown WATEKQ (package), ignoring: %s",
                package_id,
            )

    return pickings


def wamas2ubl(
    infile,
    verbose=False,
    dict_mapping_reception=False,
    dict_mapping_picking=False,
    extra_data=False,
):
    if extra_data is False:
        extra_data = {"DeliveryCustomerParty": {}, "DespatchSupplierParty": {}}

    if not dict_mapping_reception:
        dict_mapping_reception = DICT_TUPLE_KEY_RECEPTION  # noqa: F405

    if not dict_mapping_picking:
        dict_mapping_picking = DICT_TUPLE_KEY_PICKING  # noqa: F405

    # 1) parse wamas file
    data, dummy = wamas2dict(infile, verbose=verbose)
    if verbose:
        pprint(data)

    # 2) analyze/transform wamas file content
    top_keys = list(data.keys())
    top_keys.sort()
    top_keys = tuple(top_keys)
    tmpl_path = False
    if top_keys in dict_mapping_reception.keys():
        template_type = "reception"
        tmpl_path = dict_mapping_reception[top_keys][0]
        order_name = dict_mapping_reception[top_keys][1][0]
        order_key = dict_mapping_reception[top_keys][1][1]
        line_name = dict_mapping_reception[top_keys][2][0]
        line_key = dict_mapping_reception[top_keys][2][1]
        receptions = _prepare_receptions(
            data, order_name, order_key, line_name, line_key
        )
    elif top_keys in dict_mapping_picking.keys():
        template_type = "picking"
        tmpl_path = dict_mapping_picking[top_keys]
        pickings = _prepare_pickings(data)
        if verbose:
            _logger.debug("Number of pickings: %d", len(pickings))
            for order_id, picking in pickings.items():
                _logger.debug("Order ID: %s", order_id)
                _logger.debug(
                    "Number of packages: %s", len(pickings[order_id]["packages"])
                )
                pprint(picking)
    else:
        raise Exception(
            "Could not match input wamas file with a corresponding template type: %s"
            % str(top_keys)
        )

    # 3) get template
    tmpl_file = file_open(file_path(tmpl_path))
    ubl_template = tmpl_file.read()
    tmpl_file.close()

    # 4) output
    if template_type == "reception":
        ubl = []
        for reception in receptions.values():
            ubl.append(
                dict2ubl(ubl_template, reception, verbose, extra_data)  # noqa: F405
            )
    elif template_type == "picking":
        ubl = []
        for picking in pickings.values():
            ubl.append(
                dict2ubl(ubl_template, picking, verbose, extra_data)  # noqa: F405
            )
    if verbose:
        _logger.debug("Number of UBL files generated: %d", len(ubl))
        for f in ubl:
            _logger.debug(f)
    return ubl


def usage(argv):
    _logger.debug("%s -i <inputfile>" % argv[0])


def main(argv):
    infile = ""
    verbose = False
    opts, args = getopt.getopt(argv[1:], "hi:v", ["ifile=", "verbose"])
    for opt, arg in opts:
        if opt == "-h":
            usage(argv)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            infile = file_open(arg).read()
        elif opt in ("-v", "--verbose"):
            verbose = True
            logging.basicConfig(level=logging.DEBUG)
    if not infile:
        usage(argv)
        sys.exit()
    wamas2ubl(infile, verbose)


if __name__ == "__main__":
    main(sys.argv)
