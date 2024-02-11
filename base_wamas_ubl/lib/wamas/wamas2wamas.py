# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import argparse
import logging
from pprint import pformat

from . import const, utils
from .wamas2ubl import wamas2dict

_logger = logging.getLogger("wamas2wamas")


def simulate_response(dict_wamas_in):
    res = []
    line_idx = 0
    dict_parent_id = {}
    for telegram_type_in, dicts in dict_wamas_in.items():
        for telegram_type_out in const.DICT_CONVERT_WAMAS_TYPE[telegram_type_in]:
            grammar_out = const.DICT_WAMAS_GRAMMAR[telegram_type_out]
            for dict_item in dicts:
                line_idx += 1
                line = utils.generate_wamas_line(
                    dict_item,
                    grammar_out,
                    line_idx=line_idx,
                    dict_parent_id=dict_parent_id,
                    telegram_type_out=telegram_type_out,
                    do_wamas2wamas=True,
                )
                if line:
                    res.append(line)
    return res


def wamas2wamas(infile):
    data = wamas2dict(infile)
    _logger.debug(pformat(data))
    wamas_lines = simulate_response(data)
    return "\n".join(wamas_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Converts a wamas message into wamas response.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug log")
    parser.add_argument(
        "-o", "--output", dest="outputfile", help="write result in this file"
    )
    parser.add_argument("inputfile", help="read message from this file")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    infile = utils.file_open(args.inputfile).read()
    res = wamas2wamas(infile)
    if args.outputfile:
        fd = utils.file_open(args.outputfile, "w")
        fd.write(res)
    else:
        print(res)  # pylint: disable=print-used


if __name__ == "__main__":
    main()
