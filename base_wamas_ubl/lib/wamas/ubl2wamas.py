#!/usr/bin/python3

import getopt
import logging
import sys

import xmltodict
from dotty_dict import Dotty

_logger = logging.getLogger("ubl2wamas")

# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from .const import DICT_WAMAS_GRAMMAR
    from .utils import file_open, generate_wamas_line
except ImportError:
    from const import DICT_WAMAS_GRAMMAR
    from utils import file_open, generate_wamas_line


def ubl2list(infile, telegram_type):  # noqa: C901
    res = []

    my_dict = Dotty(xmltodict.parse(infile))
    lst_telegram_type = telegram_type.split(",")
    lst_to_check = ["WEAK", "WEAP", "AUSK", "AUSP", "KRETK", "KRETP"]

    if not all(x in lst_to_check for x in lst_telegram_type):
        raise Exception("Invalid telegram types: %s" % telegram_type)

    dict_telegram_type_loop = {
        "WEAP": "DespatchAdvice.cac:DespatchLine",
        "AUSP": "DespatchAdvice.cac:DespatchLine",
        "KRETP": "DespatchAdvice.cac:DespatchLine",
    }

    line_idx = 0
    for telegram_type in lst_telegram_type:
        grammar = DICT_WAMAS_GRAMMAR[telegram_type.lower()]  # noqa: F405

        loop_element = dict_telegram_type_loop.get(telegram_type, False)
        len_loop = (
            loop_element
            and isinstance(my_dict[loop_element], list)
            and len(my_dict[loop_element])
            or 1
        )

        for idx_loop in range(len_loop):
            line_idx += 1
            line = generate_wamas_line(
                my_dict,
                grammar,
                line_idx=line_idx,
                len_loop=len_loop,
                idx_loop=idx_loop,
            )
            if line:
                res.append(line)

    return res


def ubl2wamas(infile, telegram_type, verbose=False):
    lst_of_str_wamas = ubl2list(infile, telegram_type)
    wamas = "\n".join(lst_of_str_wamas)
    if verbose:
        _logger.debug(wamas)
    return wamas.encode("iso-8859-1")


def usage(argv):
    _logger.debug("%s -i <inputfile> -t <telegram_types>" % argv[0])


def main(argv):
    infile = ""
    verbose = False
    opts, args = getopt.getopt(argv[1:], "hi:t:v", ["ifile=", "teletype=", "verbose"])
    for opt, arg in opts:
        if opt == "-h":
            usage(argv)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            infile = file_open(arg).read()
        elif opt in ("-v", "--verbose"):
            verbose = True
            logging.basicConfig(level=logging.DEBUG)
        elif opt in ("-t", "--teletype"):
            telegram_type = arg
    if not infile:
        usage(argv)
        sys.exit()
    ubl2wamas(infile, telegram_type, verbose)


if __name__ == "__main__":
    main(sys.argv)
