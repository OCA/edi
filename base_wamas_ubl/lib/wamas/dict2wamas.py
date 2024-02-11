# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import argparse
import logging
from ast import literal_eval
from pprint import pformat

from . import const, utils

_logger = logging.getLogger("json2wamas")

SUPPORTED_TYPES = list(const.SUPPORTED_DICT_TO_WAMAS.keys())


def dict2list(dict_input, msg_type):
    res = []

    if msg_type not in SUPPORTED_TYPES:
        raise Exception("Invalid document type: %s" % msg_type)

    line_idx = 0
    for telegram_type in const.SUPPORTED_DICT_TO_WAMAS[msg_type]:
        grammar = const.DICT_WAMAS_GRAMMAR[telegram_type]
        # Special case for `KSTAUS`
        if telegram_type == "KSTAUS":
            # 1 line for `KstAus_LagIdKom = kMEZ`
            line_idx += 1
            dict_input["picking_zone"] = "kMEZ"
            line = utils.generate_wamas_dict(
                dict_input,
                grammar,
                line_idx=line_idx,
            )
            res.append(line)
            # 1 line for `KstAus_LagIdKom = kPAR`
            line_idx += 1
            dict_input["picking_zone"] = "kPAR"
            line = utils.generate_wamas_dict(
                dict_input,
                grammar,
                line_idx=line_idx,
            )
            res.append(line)
        else:
            line_idx += 1
            line = utils.generate_wamas_dict(
                dict_input,
                grammar,
                line_idx=line_idx,
            )
            res.append(line)
    return res


def dict2wamas(dict_input, msg_type):
    lst_of_wamas_dicts = dict2list(dict_input, msg_type)
    wamas = "\n".join(utils.wamas_dict2line(d) for d in lst_of_wamas_dicts)
    _logger.debug(lst_of_wamas_dicts)
    return wamas


def main():
    parser = argparse.ArgumentParser(
        description="Converts JSON document into message.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug log")
    parser.add_argument(
        "-f",
        "--format",
        default="wamas",
        choices=["dict", "wamas"],
        help="result format",
    )
    parser.add_argument(
        "-t", "--type", required=True, choices=SUPPORTED_TYPES, help="type of document"
    )
    parser.add_argument(
        "-o", "--output", dest="outputfile", help="write result in this file"
    )
    parser.add_argument("inputfile", help="read message from this file")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    infile = utils.file_open(args.inputfile).read()
    infile = literal_eval(infile)
    if args.format == "dict":
        res = pformat(dict2list(infile, args.type))
    else:
        res = dict2wamas(infile, args.type)
    if args.outputfile:
        fd = utils.file_open(args.outputfile, "w")
        fd.write(res)
    else:
        print(res)  # pylint: disable=print-used


if __name__ == "__main__":
    main()
