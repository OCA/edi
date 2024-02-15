# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import argparse
import logging
from pprint import pformat

import xmltodict
from dotty_dict import Dotty
from freezegun import freeze_time

from . import const, utils

_logger = logging.getLogger("ubl2wamas")

SUPPORTED_TYPES = list(const.SUPPORTED_UBL_TO_WAMAS.keys())


def ubl2list(infile, msg_type):  # noqa: C901
    res = []

    my_dict = Dotty(xmltodict.parse(infile))
    if msg_type not in SUPPORTED_TYPES:
        raise Exception("Invalid document type: %s" % msg_type)

    dict_telegram_type_loop = {
        "WEAP": "DespatchAdvice.cac:DespatchLine",
        "AUSP": "DespatchAdvice.cac:DespatchLine",
        "KRETP": "DespatchAdvice.cac:DespatchLine",
    }

    line_idx = 0
    for telegram_type in const.SUPPORTED_UBL_TO_WAMAS[msg_type]:
        grammar = const.DICT_WAMAS_GRAMMAR[telegram_type]

        loop_element = dict_telegram_type_loop.get(telegram_type, False)
        len_loop = (
            loop_element
            and isinstance(my_dict[loop_element], list)
            and len(my_dict[loop_element])
            or 1
        )

        for idx_loop in range(len_loop):
            line_idx += 1
            line = utils.generate_wamas_dict(
                my_dict,
                grammar,
                line_idx=line_idx,
                len_loop=len_loop,
                idx_loop=idx_loop,
            )
            if line:
                res.append(line)

    return res


def ubl2wamas(infile, msg_type):
    lst_of_wamas_dicts = ubl2list(infile, msg_type)
    wamas = "\n".join(utils.wamas_dict2line(d) for d in lst_of_wamas_dicts)
    _logger.debug(lst_of_wamas_dicts)
    return wamas


@freeze_time("2023-05-01")
def main():
    parser = argparse.ArgumentParser(
        description="Converts UBL document into message.",
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
    if args.format == "dict":
        res = pformat(ubl2list(infile, args.type))
    else:
        res = ubl2wamas(infile, args.type)
    if args.outputfile:
        fd = utils.file_open(args.outputfile, "w")
        fd.write(res)
    else:
        print(res)  # pylint: disable=print-used


if __name__ == "__main__":
    main()
