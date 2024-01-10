#!/usr/bin/python3

import getopt
import logging
import sys

# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from .const import (
        DICT_CONVERT_WAMAS_TYPE,
        DICT_WAMAS_GRAMMAR_OUT,
        LST_VALID_TELEGRAM_IN,
    )
    from .utils import file_open, generate_wamas_line, wamas2dict
except ImportError:
    from const import (
        DICT_CONVERT_WAMAS_TYPE,
        DICT_WAMAS_GRAMMAR_OUT,
        LST_VALID_TELEGRAM_IN,
    )
    from utils import file_open, generate_wamas_line, wamas2dict

_logger = logging.getLogger("wamas2wamas")


def _process_wamas_out(dict_wamas_in, lst_telegram_type_in):
    res = []

    if not all(x in LST_VALID_TELEGRAM_IN for x in lst_telegram_type_in):
        raise Exception("Invalid telegram types: %s" % ", ".join(lst_telegram_type_in))
    line_idx = 0
    dict_parent_id = {}
    for telegram_type_in in dict_wamas_in:
        for telegram_type_out in DICT_CONVERT_WAMAS_TYPE[telegram_type_in]:
            grammar_out = DICT_WAMAS_GRAMMAR_OUT[telegram_type_out.lower()]

            for dict_item in dict_wamas_in[telegram_type_in]:
                line_idx += 1
                line = generate_wamas_line(
                    dict_item,
                    grammar_out,
                    line_idx=line_idx,
                    dict_parent_id=dict_parent_id,
                    telegram_type_out=telegram_type_out,
                    check_to_set_value_to_string=True,
                    do_wamas2wamas=True,
                )
                if line:
                    res.append(line)

    return res


def wamas2wamas(infile, verbose=False):
    dict_wamas_in, lst_telegram_type_in = wamas2dict(
        infile, LST_VALID_TELEGRAM_IN, use_simple_grammar=True
    )
    if verbose:
        _logger.debug(dict_wamas_in)
    wamas_out_lines = _process_wamas_out(dict_wamas_in, lst_telegram_type_in)
    wamas_out = "\n".join(wamas_out_lines)
    if verbose:
        # `print` is used to output to file
        print(wamas_out)  # pylint: disable=print-used
    return wamas_out


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
    wamas2wamas(infile, verbose)


if __name__ == "__main__":
    main(sys.argv)
