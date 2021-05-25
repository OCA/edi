#! /usr/bin/python3
# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Mass import of PDF/XML invoice.
The module OCA/edi/account_invoice_import must be installed on Odoo.
"""
import argparse
import base64
import getpass
import logging
import mimetypes
import os
import sys

import odoorpc

__author__ = "Alexis de Lattre <alexis.delattre@akretion.com>"
__date__ = "March 2021"
__version__ = "0.2"

FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("add_xivo_user")

fail_subdir_ok = {}  # key = directory, value: failsubdir or False
invoice_ids = []
fail_files = []


def send_file(odoo, file_path):
    filename = os.path.basename(file_path)
    filetype = mimetypes.guess_type(filename)
    logger.debug("filetype of file %s=%s", filename, filetype)
    inv_mime = ["application/xml", "text/xml", "application/pdf"]
    if filetype and filetype[0] in inv_mime:
        logger.info("Starting to upload file %s to Odoo", filename)
        if not os.access(file_path, os.R_OK):
            logger.error("No read access on file %s. Skipping.", filename)
            return False
        with open(file_path, "rb") as f:
            f.seek(0)
            invoice = f.read()
        inv_b64 = base64.encodebytes(invoice)
        aiio = odoo.env["account.invoice.import"]
        try:
            invoice_id = aiio.create_invoice_webservice(
                inv_b64.decode("utf8"), filename, "mass import script"
            )
            if invoice_id:
                logger.info("Invoice ID %d successfully created in Odoo", invoice_id)
                invoice_ids.append(invoice_id)
                return "success"
            else:
                logger.warning("Invoice import failed")
                fail_files.append(filename)
                return "failure"
        except Exception as e:
            logger.warning("Odoo failed to import file %s. Reason: %s", filename, e)
            fail_files.append(filename)
            return "failure"
    else:
        logger.warning("Filetype of file %s is %s. Skipping.", filename, filetype)
        return False


def update_fail_subdir(directory, fail_subdir):
    fail_subdir_ok[directory] = False
    # We need write access on directory not only to create a sub-dir but also
    # to move files out of it
    if not os.access(directory, os.W_OK):
        logger.warning(
            "No permission to create a sub-directory nor remove "
            "files from %s. Disabling the move-to-faildir feature "
            "for that directory.",
            directory,
        )
        return False
    fail_dir_path = os.path.join(directory, fail_subdir)
    if not os.path.exists(fail_dir_path):
        logger.info("Creating sub-directory %s", fail_subdir)
        os.makedirs(fail_dir_path)
    if not os.access(fail_dir_path, os.W_OK):
        logger.warning(
            "No permission to move files to %s. Disabling the move-to-faildir"
            "feature for directory %s",
            fail_dir_path,
            directory,
        )
        return False
    fail_subdir_ok[directory] = fail_dir_path
    return True


def handle_failure(directory, entry, file_path):
    if not args.no_move_failed:
        if directory not in fail_subdir_ok:
            update_fail_subdir(directory, args.fail_subdir)
        fail_dir_path = fail_subdir_ok[directory]
        if fail_dir_path:
            logger.info(
                "Moving file %s to sub-directory %s",
                entry,
                args.fail_subdir,
            )
            os.rename(file_path, os.path.join(fail_dir_path, entry))


def browse_directory(odoo, directory):
    if os.path.isdir(directory):
        logger.info("Start working on directory %s", directory)
        for entry in os.listdir(directory):
            file_path = os.path.join(directory, entry)
            logger.debug("file_path=%s", entry)
            if not os.path.isfile(file_path):
                continue
            res = send_file(odoo, file_path)
            if res == "failure":
                handle_failure(directory, entry, file_path)

    elif os.path.isfile(directory):
        res = send_file(odoo, directory)
    else:
        logger.warning("%s is not a directory nor a file. Skipped." % directory)


def main(args):
    if args.log_level:
        log_level = args.log_level.lower()
        log_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARN,
            "error": logging.ERROR,
        }
        if log_level in log_map:
            logger.setLevel(log_map[log_level])
        else:
            logger.error(
                "Wrong value for log level (%s). Possible values: "
                "debug, info, warn, error.",
                log_level,
            )
            sys.exit(1)
    pwd = args.password
    first_login = True
    while not pwd:
        # prompt for password
        pwd = getpass.getpass()
        if first_login:
            logger.error("Cannot connect with an empty password. Re-enter a password.")
        first_login = False
    if not args:
        logger.error(
            "Missing directory argument. You should pass to the "
            "script at least one directory as argument."
        )
        sys.exit(1)
    proto = args.no_ssl and "jsonrpc" or "jsonrpc+ssl"
    logger.info(
        "Connecting to Odoo %s:%s in %s database %s username %s",
        args.server,
        args.port,
        proto,
        args.database,
        args.username,
    )
    try:
        odoo = odoorpc.ODOO(args.server, proto, args.port)
        odoo.login(args.database, args.username, pwd)
        logger.info("Successfully connected to Odoo")
    except Exception as e:
        logger.error("Failed to connect to Odoo. Error: %s", e)
        sys.exit(1)

    for directory in args.dir_list:
        browse_directory(odoo, directory)
    logger.info(
        "RESULT: %d invoice%s created in Odoo, %d invoice import failure%s.",
        len(invoice_ids),
        len(invoice_ids) > 1 and "s" or "",
        len(fail_files),
        len(fail_files) > 1 and "s" or "",
    )
    logger.debug("IDs of created invoices: %s", invoice_ids)
    logger.debug("Fail invoice imports: %s", fail_files)


if __name__ == "__main__":
    usage = (
        "Usage: mass_invoice_import.py [options] directory1 directory2 "
        "directory3 ..."
    )
    epilog = (
        "Script written by Alexis de Lattre. " "Published under the GNU AGPL licence."
    )
    description = (
        "This script is designed for mass import of "
        "PDF or XML invoices in Odoo. The OCA module account_invoice_import "
        "must be installed on Odoo together with the module(s) that add "
        "support for the specific invoice format."
    )
    parser = argparse.ArgumentParser(
        usage=usage, epilog=epilog, description=description
    )
    parser.add_argument(
        "-s",
        "--server",
        dest="server",
        type=str,
        required=True,
        help="DNS or IP address of the Odoo server.",
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=443,
        help="Port of Odoo's HTTP(S) interface. Default: 443.",
    )
    parser.add_argument(
        "-x",
        "--no-ssl",
        dest="no_ssl",
        action="store_true",
        help="Use un-encrypted HTTP connection instead of HTTPS.",
    )
    parser.add_argument(
        "-d",
        "--database",
        dest="database",
        type=str,
        required=True,
        help="Odoo database name.",
    )
    parser.add_argument(
        "-u",
        "--username",
        dest="username",
        type=str,
        required=True,
        help="Username to use when connecting to Odoo.",
    )
    parser.add_argument(
        "-w",
        "--password",
        dest="password",
        type=str,
        required=True,
        help="Password of the Odoo user. If you don't use this option, "
        "the script will prompt you for a password.",
    )
    parser.add_argument(
        "-m",
        "--no-move-fail",
        dest="no_move_failed",
        action="store_true",
        help="Don't move failed invoices to a fail sub-directory.",
    )
    parser.add_argument(
        "-k",
        "--fail-subdir-name",
        dest="fail_subdir",
        type=str,
        default="odoo-import_fail",
        help="Fail sub-directory name. Default value: 'odoo-import_fail'.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        default="info",
        type=str,
        help="Set log level. Possible values: debug, info, warn, error. "
        "Default value: info.",
    )
    parser.add_argument("dir_list", help="List of directories", type=str, nargs="+")
    args = parser.parse_args()
    main(args)
