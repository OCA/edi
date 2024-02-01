
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=13.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=13.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A13.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=13.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A13.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# EDI modules

None

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_e-invoice_generate](account_e-invoice_generate/) | 13.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Technical module to generate PDF invoices with embedded XML file
[account_invoice_export](account_invoice_export/) | 13.0.1.2.2 |  | Account Invoice Export
[account_invoice_export_server_env](account_invoice_export_server_env/) | 13.0.1.0.2 |  | Server environment for Account Invoice Export
[account_invoice_facturx](account_invoice_facturx/) | 13.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 13.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_ubl](account_invoice_ubl/) | 13.0.1.1.0 |  | Generate UBL XML file for customer invoices/refunds
[account_invoice_ubl_email_attachment](account_invoice_ubl_email_attachment/) | 13.0.1.1.1 |  | Automatically adds the UBL file to the email.
[account_invoice_ubl_peppol](account_invoice_ubl_peppol/) | 13.0.1.1.0 |  | Generate invoices in PEPPOL 3.0 BIS dialect
[base_business_document_import](base_business_document_import/) | 13.0.2.1.1 |  | Provides technical tools to import sale orders or supplier invoices
[base_ebill_payment_contract](base_ebill_payment_contract/) | 13.0.1.0.0 |  | Base for managing e-billing contracts
[base_edi](base_edi/) | 13.0.1.0.3 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 13.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 13.0.2.5.1 |  | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 13.0.1.0.1 |  | Payment-related code for Universal Business Language (UBL)
[edi](edi/) | 13.0.1.24.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_account](edi_account/) | 13.0.2.0.1 |  | Define EDI Configuration for Account Moves
[edi_backend_partner](edi_backend_partner/) | 13.0.1.0.1 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | add the a partner field in EDI backend
[edi_bank_statement_oca](edi_bank_statement_oca/) | 13.0.1.0.0 |  | Define EDI Configuration for Bank Statements
[edi_exchange_template](edi_exchange_template/) | 13.0.1.7.2 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allows definition of exchanges via templates.
[edi_purchase_oca](edi_purchase_oca/) | 13.0.1.0.0 |  | Define EDI Configuration for Purchase Orders
[edi_stock_oca](edi_stock_oca/) | 13.0.1.1.0 |  | Define EDI Configuration for Stock
[edi_storage](edi_storage/) | 13.0.1.8.2 |  | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_voxel](edi_voxel/) | 13.0.1.0.3 |  | Base module for connecting with Voxel
[edi_voxel_account_invoice](edi_voxel_account_invoice/) | 13.0.1.1.3 |  | Sends account invoices to Voxel.
[edi_voxel_sale_order_import](edi_voxel_sale_order_import/) | 13.0.1.0.7 |  | Import sale order from Voxel.
[edi_voxel_sale_secondary_unit](edi_voxel_sale_secondary_unit/) | 13.0.1.0.0 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Map Voxel UoM to Sale Secondary UoM and Use Them
[edi_voxel_secondary_unit](edi_voxel_secondary_unit/) | 13.0.1.0.0 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Add Voxel UoM code to Secondary UoM model
[edi_voxel_stock_picking](edi_voxel_stock_picking/) | 13.0.1.0.5 |  | Sends stock picking report to Voxel.
[edi_voxel_stock_picking_secondary_unit](edi_voxel_stock_picking_secondary_unit/) | 13.0.1.0.1 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Export Secondary UoMs Voxel Code in picking Voxel documents
[edi_webservice](edi_webservice/) | 13.0.1.2.2 |  | Defines webservice integration from EDI Exchange records
[edi_xml](edi_xml/) | 13.0.1.2.2 |  | Base module for EDI exchange using XML files.
[partner_identification_import](partner_identification_import/) | 13.0.2.0.1 |  | Provides partner matching on extra ID
[purchase_order_ubl](purchase_order_ubl/) | 13.0.1.2.1 |  | Embed UBL XML file inside the PDF purchase order
[purchase_stock_ubl](purchase_stock_ubl/) | 13.0.1.1.1 |  | Glue module for Purchase Order UBL and Stock/Inventory
[sale_order_customer_free_ref](sale_order_customer_free_ref/) | 13.0.1.0.1 |  | Splits the Customer Reference on sale orders into two fields. An Id and a Free reference. The existing field is transformed into a computed one.
[sale_order_import](sale_order_import/) | 13.0.2.1.2 |  | Import RFQ or sale orders from files
[sale_order_import_ubl](sale_order_import_ubl/) | 13.0.2.2.0 |  | Import UBL XML sale order files
[sale_order_import_ubl_customer_free_ref](sale_order_import_ubl_customer_free_ref/) | 13.0.1.0.1 |  | Extract CustomerReference from sale UBL
[sale_order_import_ubl_http](sale_order_import_ubl_http/) | 13.0.1.1.3 |  | Add an HTTP endpoint to import UBL formatted ordersautomatically as sales order
[sale_order_ubl](sale_order_ubl/) | 13.0.1.1.0 |  | Embed UBL XML file inside the PDF quotation
[webservice](webservice/) | 13.0.1.0.2 |  | Defines webservice abstract definition to be used generally

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
