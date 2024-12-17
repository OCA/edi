# SPDX-FileCopyrightText: 2021 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Account Invoice Files Download",
    "summary": "Allow to download all files of invoices as one zip file",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_edi",
    ],
    "data": [
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
    ],
}
