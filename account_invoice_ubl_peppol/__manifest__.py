# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice UBL PEPPOL",
    "summary": "Generate invoices in PEPPOL 3.0 BIS dialect",
    "version": "14.0.1.0.2",
    "category": "Accounting & Finance",
    "author": "Sunflower IT, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "depends": ["account_invoice_ubl", "partner_coc", "base_iban"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "views/peppol_eas_list.xml",
        "data/peppol.eas.list.csv",
        "views/res_country.xml",
    ],
    "installable": True,
}
