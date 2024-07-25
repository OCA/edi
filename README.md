
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=12.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=12.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A12.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=12.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A12.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/12.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-12-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-12-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Electronic Data Interchange modules

Electronic Data Interchange modules

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_e-invoice_generate](account_e-invoice_generate/) | 12.0.1.1.0 |  | Technical module to generate PDF invoices with embedded XML file
[account_invoice_download](account_invoice_download/) | 12.0.1.0.0 |  | Auto-download supplier invoices and import them
[account_invoice_download_ovh](account_invoice_download_ovh/) | 12.0.1.0.1 |  | Get OVH Invoice via the API
[account_invoice_facturx](account_invoice_facturx/) | 12.0.1.1.1 |  | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 12.0.1.0.0 |  | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_import](account_invoice_import/) | 12.0.1.1.1 |  | Import supplier invoices/refunds as PDF or XML files
[account_invoice_import_facturx](account_invoice_import_facturx/) | 12.0.1.0.1 |  | Import Factur-X/ZUGFeRD supplier invoices/refunds
[account_invoice_import_invoice2data](account_invoice_import_invoice2data/) | 12.0.1.1.1 |  | Import supplier invoices using the invoice2data lib
[account_invoice_import_ubl](account_invoice_import_ubl/) | 12.0.1.0.1 |  | Import UBL XML supplier invoices/refunds
[account_invoice_ubl](account_invoice_ubl/) | 12.0.1.1.2 |  | Generate UBL XML file for customer invoices/refunds
[account_invoice_ubl_email_attachment](account_invoice_ubl_email_attachment/) | 12.0.1.0.2 |  | Automatically adds the UBL file to the email.
[base_business_document_import](base_business_document_import/) | 12.0.1.0.1 |  | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 12.0.1.0.0 |  | Use phone numbers to match partners upon import of business documents
[base_business_document_import_stock](base_business_document_import_stock/) | 12.0.1.0.1 |  | Match incoterms upon import of business documents
[base_edi](base_edi/) | 12.0.1.0.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 12.0.1.0.0 |  | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 12.0.1.1.2 |  | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 12.0.1.0.1 |  | Payment-related code for Universal Business Language (UBL)
[edi_oca](edi_oca/) | 12.0.1.22.4 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[purchase_order_ubl](purchase_order_ubl/) | 12.0.1.0.1 |  | Embed UBL XML file inside the PDF purchase order
[purchase_stock_ubl](purchase_stock_ubl/) | 12.0.1.0.1 |  | Glue module for Purchase Order UBL and Stock/Inventory
[sale_order_import](sale_order_import/) | 12.0.1.0.1 |  | Import RFQ or sale orders from files
[sale_order_ubl](sale_order_ubl/) | 12.0.1.0.1 |  | Embed UBL XML file inside the PDF quotation

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
