#! /bin/sh
# -*- coding: utf-8 -*-
# Copyright 2019 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# This script is designed to run under Linux
# To install the required tools, run:
# sudo apt install inotify-tools

# CUSTOMIZE the 2 variables below
INVOICE_DIR="/home/alexis/invoices2odoo"
MASS_INVOICE_IMPORT_SCRIPT="/home/alexis/edi/account_invoice_import/scripts/mass_invoice_import.py"

echo "Start to monitor $INVOICE_DIR for new files"

inotifywait -m -e create -e moved_to --format "%e %w%f" "$INVOICE_DIR" |
    while read event filepath; do
        if [ -f "$filepath" ]; then
            echo "File '$filepath' appeared via $event"
            # do something with the file
            "$MASS_INVOICE_IMPORT_SCRIPT" -s localhost -p 8069 -x -d o0_weboob2 -u admin -w admin "$filepath"
        fi
    done
