# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Electronic invoices with UBL/CII - UNECE payments",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "license": "AGPL-3",
    "summary": "Import/Export UNECE payment codes in UBL and CII XML documents.",
    "author": "BCIM, Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # Odoo
        "account_edi_ubl_cii",
        # OCA/community-data-files
        "account_payment_unece",
    ],
    "data": [
        "data/account_payment_method.xml",
    ],
    "installable": True,
    "auto_install": True,
}
