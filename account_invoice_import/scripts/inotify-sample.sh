#! /bin/sh
# -*- coding: utf-8 -*-
# Copyright 2019-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# This script is designed to run under Linux
# To install the required tools, run:
# sudo apt install inotify-tools

# CUSTOMIZE the variables below
INVOICE_DIR="/home/alexis/invoices2odoo"
MASS_INVOICE_IMPORT_SCRIPT="/usr/local/bin/mass_invoice_import.py"
ODOO_SERVER="localhost"
ODOO_PORT=8069
ODOO_DB="o4_test1"
ODOO_LOGIN="admin"
ODOO_PASSWORD="admin"

echo "Start to monitor $INVOICE_DIR for new files"

inotifywait -m -e create -e moved_to --format "%e %w%f" "$INVOICE_DIR" |
    while read event filepath; do
        if [ -f "$filepath" ]; then
            echo "File '$filepath' appeared via $event"
            # do something with the file
            "$MASS_INVOICE_IMPORT_SCRIPT" -s "$ODOO_SERVER" -p $ODOO_PORT -x -d "$ODOO_DB" -u "$ODOO_LOGIN" -w "$ODOO_PASSWORD" "$filepath"
        fi
    done
