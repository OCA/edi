
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# edi
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

TODO: add repo description.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_edi_no_autocreate_partner](account_edi_no_autocreate_partner/) | 16.0.1.0.0 |  | Prevents auto-creation of partners during invoice import by assigning unmatched invoices to a protected “Partner Not Found” contact.
[account_edi_no_product_name_match](account_edi_no_product_name_match/) | 16.0.1.0.0 |  | Disable product matching by name in Account EDI imports
[account_edi_ubl_cii_supplier_invoice_number](account_edi_ubl_cii_supplier_invoice_number/) | 16.0.1.0.0 |  | This addon extends the UBL invoice import process to automatically populate the suppliers invoice number based on the value found in the XML file.
[account_einvoice_generate](account_einvoice_generate/) | 16.0.1.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Technical module to generate PDF invoices with embedded XML file
[account_invoice_download](account_invoice_download/) | 16.0.1.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Auto-download supplier invoices and import them
[account_invoice_download_ovh](account_invoice_download_ovh/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Get OVH Invoice via the API
[account_invoice_edifact](account_invoice_edifact/) | 16.0.1.0.0 |  | Generate customer invoices with EDIFACT/D96A format
[account_invoice_export](account_invoice_export/) | 16.0.1.0.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Account Invoice Export
[account_invoice_export_job](account_invoice_export_job/) | 16.0.1.0.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Account Invoice Export Job
[account_invoice_facturx](account_invoice_facturx/) | 16.0.2.0.1 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_import](account_invoice_import/) | 16.0.2.5.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import supplier invoices/refunds as PDF or XML files
[account_invoice_import_facturx](account_invoice_import_facturx/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import Factur-X/ZUGFeRD Vendor Bills
[account_invoice_import_simple_pdf](account_invoice_import_simple_pdf/) | 16.0.1.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import simple PDF vendor bills
[account_invoice_import_ubl](account_invoice_import_ubl/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import UBL XML supplier invoices/refunds
[account_invoice_ubl](account_invoice_ubl/) | 16.0.1.0.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Generate UBL XML file for customer invoices/refunds
[base_business_document_import](base_business_document_import/) | 16.0.1.3.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Use phone numbers to match partners upon import of business documents
[base_ebill_payment_contract](base_ebill_payment_contract/) | 16.0.1.0.2 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Base for managing e-billing contracts
[base_edi](base_edi/) | 16.0.1.1.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Base module to aggregate EDI features.
[base_edifact](base_edifact/) | 16.0.1.5.1 | <a href='https://github.com/rmorant'><img src='https://github.com/rmorant.png' width='32' height='32' style='border-radius:50%;' alt='rmorant'/></a> | UN/EDIFACT/D96A utilities using pydifact parser
[base_facturx](base_facturx/) | 16.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 16.0.1.2.1 |  | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 16.0.1.0.1 |  | Payment-related code for Universal Business Language (UBL)
[base_wamas_ubl](base_wamas_ubl/) | 16.0.1.17.1 |  | Base module to aggregate WAMAS - UBL features.
[despatch_advice_import](despatch_advice_import/) | 16.0.1.2.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Despatch Advice import
[despatch_advice_import_ubl](despatch_advice_import_ubl/) | 16.0.1.1.0 |  | Import Despatch Advice files
[pdf_helper](pdf_helper/) | 16.0.1.1.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Provides helpers to work w/ PDFs
[sale_order_import](sale_order_import/) | 16.0.1.5.0 |  | Import RFQ or sale orders from files
[sale_order_import_edifact](sale_order_import_edifact/) | 16.0.1.1.0 | <a href='https://github.com/rmorant'><img src='https://github.com/rmorant.png' width='32' height='32' style='border-radius:50%;' alt='rmorant'/></a> | EDIFACT/D96A Order

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
