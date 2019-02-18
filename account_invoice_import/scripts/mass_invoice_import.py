#! /usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2017-2019 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Mass import of PDF/XML invoice.
The module OCA/edi/account_invoice_import must be installed on Odoo.
Can be combined with the script inotify-sample.sh to auto-push
invoices to Odoo upon saving the invoice in a special directory.
"""

import odoorpc
import sys
from optparse import OptionParser
import logging
import os
import getpass
import mimetypes

__author__ = "Alexis de Lattre <alexis.delattre@akretion.com>"
__date__ = "February 2019"
__version__ = "0.2"

FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('add_xivo_user')
# Define command line options
options = [
    {'names': ('-s', '--server'), 'dest': 'server', 'type': 'string',
        'action': 'store', 'default': False,
        'help': 'DNS or IP address of the Odoo server.'},
    {'names': ('-p', '--port'), 'dest': 'port', 'type': 'int',
        'action': 'store', 'default': 443,
        'help': "Port of Odoo's HTTP(S) interface. Default: 443."},
    {'names': ('-x', '--no-ssl'), 'dest': 'no_ssl',
        'help': "Use un-encrypted HTTP connection instead of HTTPS.",
        'action': 'store_true', 'default': False},
    {'names': ('-d', '--database'), 'dest': 'database', 'type': 'string',
        'action': 'store', 'default': False,
        'help': "Odoo database name."},
    {'names': ('-u', '--username'), 'dest': 'username', 'type': 'string',
        'action': 'store', 'default': False,
        'help': "Username to use when connecting to Odoo."},
    {'names': ('-w', '--password'), 'dest': 'password', 'type': 'string',
        'action': 'store', 'default': False,
        'help': "Password of the Odoo user. If you don't use this option, "
        "the script will prompt you for a password."},
    {'names': ('-m', '--no-move'), 'dest': 'no_move',
        'action': 'store_true', 'default': False,
        'help': "Don't move invoices to failure or success sub-directories."},
    {'names': ('-j', '--success-subdir-name'), 'dest': 'success_subdir',
        'action': 'store', 'default': 'success',
        'help': "Success sub-directory name. Default value: 'success'."},
    {'names': ('-k', '--failure-subdir-name'), 'dest': 'failure_subdir',
        'action': 'store', 'default': 'failure',
        'help': "Failure sub-directory name. Default value: 'failure'."},
    {'names': ('-l', '--log-level'), 'dest': 'log_level',
        'action': 'store', 'default': 'info',
        'help': "Set log level. Possible values: debug, info, warn, error. "
        "Default value: info."},
]
fail_subdir_ok = {}  # key = directory, value: failsubdir or False
invoice_ids = []
fail_files = []


def send_file(odoo, file_path, success_dir_path, failure_dir_path):
    filename = os.path.basename(file_path)
    filetype = mimetypes.guess_type(filename)
    logger.debug('filetype of file %s=%s', filename, filetype)
    inv_mime = ['application/xml', 'text/xml', 'application/pdf']
    if filetype and filetype[0] in inv_mime:
        logger.info("Starting to upload file '%s' to Odoo", filename)
        if not os.access(file_path, os.R_OK):
            logger.error("No read access on file '%s'. Skipping.", filename)
            return False
        f = open(file_path)
        f.seek(0)
        invoice = f.read()
        f.close()
        aiio = odoo.env['account.invoice.import']
        try:
            inv_id = aiio.invoice_import_direct_ws(
                invoice.encode('base64'), filename)
            if inv_id:
                logger.info(
                    'Invoice ID %d successfully created in Odoo', inv_id)
                invoice_ids.append(inv_id)
                move_file_to(file_path, success_dir_path)
                return 'success'
            else:
                logger.debug("inv_id=%s", inv_id)
                logger.warning('Failed to create invoice')
                fail_files.append(filename)
                move_file_to(file_path, failure_dir_path)
                return 'failure'
        except Exception, e:
            logger.warning(
                "Odoo failed to import file '%s'. Reason: '%s'.", filename, e)
            fail_files.append(filename)
            move_file_to(file_path, failure_dir_path)
            return 'failure'
    else:
        logger.warning(
            "Filetype of file '%s' is '%s'. Skipping.", filename, filetype)
        return False


def move_file_to(file_path, to_dir_path):
    if not options.no_move:
        logger.info(
            "Moving file '%s' to sub-directory '%s'",
            file_path, os.path.split(to_dir_path)[1])
        os.rename(
            file_path,
            os.path.join(to_dir_path, os.path.basename(file_path)))


def update_subdir(directory, subdir):
    fail_subdir_ok[directory] = False
    # We need write access on directory not only to create a sub-dir but also
    # to move files out of it
    if not os.access(directory, os.W_OK):
        logger.warning(
            "No permission to create a sub-directory nor remove "
            "files from '%s'. Cannot use the move-to feature. Exiting.",
            directory)
        return sys.exit(1)
    dir_path = os.path.join(directory, subdir)
    if not os.path.exists(dir_path):
        logger.info("Creating sub-directory '%s'", subdir)
        os.makedirs(dir_path)
    if not os.access(dir_path, os.W_OK):
        logger.warning(
            "No permission to move files to '%s'. Cannot use the move-to "
            "feature. Exiting.", dir_path, directory)
        return sys.exit(1)
    return dir_path


def success_failure_update_subdir(directory):
    failure_dir_path = update_subdir(
        directory, options.failure_subdir)
    success_dir_path = update_subdir(
        directory, options.success_subdir)
    return (success_dir_path, failure_dir_path)


def main(options, arguments):
    # print 'options = %s' % options
    # print 'arguments = %s' % arguments
    if options.log_level:
        log_level = options.log_level.lower()
        log_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warn': logging.WARN,
            'error': logging.ERROR,
        }
        if log_level in log_map:
            logger.setLevel(log_map[log_level])
        else:
            logger.error(
                'Wrong value for log level (%s). Possible values: '
                'debug, info, warn, error.', log_level)
            sys.exit(1)
    if not options.username:
        logger.error('Missing username: use the -u command line option.')
        sys.exit(1)
    if not options.server:
        logger.error("Missing server: use the -s command line option.")
        sys.exit(1)
    if not options.database:
        logger.error("Missing database name: use the -d command line option.")
        sys.exit(1)
    pwd = options.password
    first_login = True
    while not pwd:
        # prompt for password
        pwd = getpass.getpass()
        if first_login:
            logger.error(
                "Cannot connect with an empty password. Re-enter a password.")
        first_login = False
    if not arguments:
        logger.error(
            "Missing directory argument. You should pass to the "
            "script at least one directory as argument.")
        sys.exit(1)
    proto = options.no_ssl and 'jsonrpc' or 'jsonrpc+ssl'
    logger.info(
        "Connecting to Odoo %s:%s in %s database %s username %s",
        options.server, options.port, proto, options.database,
        options.username)
    try:
        odoo = odoorpc.ODOO(options.server, proto, options.port)
        odoo.login(options.database, options.username, pwd)
        logger.debug('Successfully connected to Odoo')
    except Exception, e:
        logger.error("Failed to connect to Odoo. Error: %s", e)
        sys.exit(1)

    for directory in arguments:
        if os.path.isdir(directory):
            logger.info("Start working on directory '%s'", directory)
            if not options.no_move:
                success_dir_path, failure_dir_path =\
                    success_failure_update_subdir(directory)
            for entry in os.listdir(directory):
                file_path = os.path.join(directory, entry)
                logger.debug('file_path=%s', entry)
                if os.path.isfile(file_path):
                    send_file(
                        odoo, file_path, success_dir_path, failure_dir_path)
        elif os.path.isfile(directory):
            inv_filepath = directory
            directory = os.path.dirname(inv_filepath)
            success_dir_path, failure_dir_path =\
                success_failure_update_subdir(directory)
            send_file(odoo, inv_filepath, success_dir_path, failure_dir_path)
        else:
            logger.warning(
                "'%s' is not a directory nor a file. Skipped." % directory)
    logger.info(
        'RESULT: %d invoice%s created in Odoo, %d invoice import failure%s.',
        len(invoice_ids), len(invoice_ids) > 1 and 's' or '',
        len(fail_files), len(fail_files) > 1 and 's' or '')
    logger.debug('IDs of created invoices: %s', invoice_ids)
    logger.debug('Fail invoice imports: %s', fail_files)


if __name__ == '__main__':
    usage = "Usage: mass_invoice_import.py [options] directory1 directory2 "\
        "directory3 ..."
    epilog = "Script written by Alexis de Lattre. "\
        "Published under the GNU AGPL licence."
    description = "This script is designed for mass import of "\
        "PDF or XML invoices in Odoo. The OCA module account_invoice_import "\
        "must be installed on Odoo together with the module(s) that add "\
        "support for the specific invoice format."
    parser = OptionParser(usage=usage, epilog=epilog, description=description)
    for option in options:
        param = option['names']
        del option['names']
        parser.add_option(*param, **option)
    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
