#!/usr/bin/python3

import getopt
import logging
import sys
from pprint import pprint

_logger = logging.getLogger("check_wamas")

# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from .utils import detect_wamas_type, file_open
except ImportError:
    from utils import detect_wamas_type, file_open


def check_wamas(infile, verbose=False):
    data, lst_telegram_type, wamas_type = detect_wamas_type(infile)
    if verbose:
        pprint(lst_telegram_type)
        pprint(wamas_type)
        pprint(data)
    return data, lst_telegram_type, wamas_type


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
            infile = file_open(arg).read()  # noqa: F405
        elif opt in ("-v", "--verbose"):
            verbose = True
            logging.basicConfig(level=logging.DEBUG)
    if not infile:
        usage(argv)
        sys.exit()
    check_wamas(infile, verbose)


if __name__ == "__main__":
    main(sys.argv)
