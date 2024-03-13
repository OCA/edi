
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# edi

Electronic Data Interchange modules

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_einvoice_generate](account_einvoice_generate/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Technical module to generate PDF invoices with embedded XML file
[account_invoice_download](account_invoice_download/) | 14.0.1.0.2 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Auto-download supplier invoices and import them
[account_invoice_download_ovh](account_invoice_download_ovh/) | 14.0.1.1.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Get OVH Invoice via the API
[account_invoice_download_scaleway](account_invoice_download_scaleway/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Get Scaleway Invoices via the API
[account_invoice_export](account_invoice_export/) | 14.0.1.2.4 |  | Account Invoice Export
[account_invoice_export_server_env](account_invoice_export_server_env/) | 14.0.1.0.0 |  | Server environment for Account Invoice Export
[account_invoice_facturx](account_invoice_facturx/) | 14.0.1.1.2 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_import](account_invoice_import/) | 14.0.3.3.2 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import supplier invoices/refunds as PDF or XML files
[account_invoice_import_facturx](account_invoice_import_facturx/) | 14.0.1.0.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import Factur-X/ZUGFeRD supplier invoices/refunds
[account_invoice_import_invoice2data](account_invoice_import_invoice2data/) | 14.0.2.3.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) [![bosd](https://github.com/bosd.png?size=30px)](https://github.com/bosd) | Import supplier invoices using the invoice2data lib
[account_invoice_import_simple_pdf](account_invoice_import_simple_pdf/) | 14.0.3.3.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import simple PDF vendor bills
[account_invoice_import_ubl](account_invoice_import_ubl/) | 14.0.1.0.1 |  | Import UBL XML supplier invoices/refunds
[account_invoice_ubl](account_invoice_ubl/) | 14.0.1.0.3 |  | Generate UBL XML file for customer invoices/refunds
[account_invoice_ubl_email_attachment](account_invoice_ubl_email_attachment/) | 14.0.1.0.0 |  | Automatically adds the UBL file to the email.
[account_invoice_ubl_peppol](account_invoice_ubl_peppol/) | 14.0.1.0.2 |  | Generate invoices in PEPPOL 3.0 BIS dialect
[base_business_document_import](base_business_document_import/) | 14.0.3.2.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Use phone numbers to match partners upon import of business documents
[base_ebill_payment_contract](base_ebill_payment_contract/) | 14.0.1.1.0 | [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Base for managing e-billing contracts
[base_edi](base_edi/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 14.0.1.8.2 |  | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 14.0.1.0.0 |  | Payment-related code for Universal Business Language (UBL)
[edi_account_invoice_import](edi_account_invoice_import/) | 14.0.1.1.0 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | Plug account_invoice_import into EDI machinery.
[edi_account_oca](edi_account_oca/) | 14.0.1.1.1 |  | Define EDI Configuration for Account Moves
[edi_backend_partner_oca](edi_backend_partner_oca/) | 14.0.1.0.1 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | add the a partner field in EDI backend
[edi_endpoint_oca](edi_endpoint_oca/) | 14.0.1.5.0 |  | Base module allowing configuration of custom endpoints for EDI framework.
[edi_exchange_template_oca](edi_exchange_template_oca/) | 14.0.1.5.2 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allows definition of exchanges via templates.
[edi_exchange_template_party_data](edi_exchange_template_party_data/) | 14.0.1.0.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Glue module betweeb edi_exchange_template and edi_party_data
[edi_oca](edi_oca/) | 14.0.1.22.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_party_data_oca](edi_party_data_oca/) | 14.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allow to configure and retrieve party information for EDI exchanges.
[edi_pdf2data_oca](edi_pdf2data_oca/) | 14.0.1.0.1 | [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Module that allows to import data from a pdf
[edi_purchase_oca](edi_purchase_oca/) | 14.0.1.0.0 |  | Define EDI Configuration for Purchase Orders
[edi_sale_order_import](edi_sale_order_import/) | 14.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Plug sale_order_import into EDI machinery.
[edi_sale_order_import_ubl](edi_sale_order_import_ubl/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Plug sale_order_import_ubl into EDI machinery.
[edi_sale_order_import_ubl_endpoint](edi_sale_order_import_ubl_endpoint/) | 14.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Provide a default endpoint to import SO in UBL format.
[edi_stock_oca](edi_stock_oca/) | 14.0.1.0.0 |  | Define EDI Configuration for Stock
[edi_storage_oca](edi_storage_oca/) | 14.0.1.8.1 |  | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_ubl_oca](edi_ubl_oca/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Define EDI backend type for UBL.
[edi_voxel_oca](edi_voxel_oca/) | 14.0.1.0.0 |  | Base module for connecting with Voxel
[edi_webservice_oca](edi_webservice_oca/) | 14.0.1.4.1 | [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Defines webservice integration from EDI Exchange records
[edi_xml_oca](edi_xml_oca/) | 14.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module for EDI exchange using XML files.
[partner_identification_import](partner_identification_import/) | 14.0.1.0.1 |  | Provides partner matching on extra ID
[pdf_helper](pdf_helper/) | 14.0.1.2.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides helpers to work w/ PDFs
[product_import](product_import/) | 14.0.1.2.0 |  | Import product catalogues
[product_import_ubl](product_import_ubl/) | 14.0.1.1.1 |  | Import UBL XML catalogue files
[purchase_order_ubl](purchase_order_ubl/) | 14.0.1.1.1 |  | Embed UBL XML file inside the PDF purchase order
[purchase_order_ubl_py3o](purchase_order_ubl_py3o/) | 14.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate UBL purchase orders with Py3o reporting engine
[purchase_stock_ubl](purchase_stock_ubl/) | 14.0.1.0.0 |  | Glue module for Purchase Order UBL and Stock/Inventory
[sale_order_customer_free_ref](sale_order_customer_free_ref/) | 14.0.1.0.0 |  | Splits the Customer Reference on sale orders into two fields. An Id and a Free reference. The existing field is transformed into a computed one.
[sale_order_import](sale_order_import/) | 14.0.1.5.0 |  | Import RFQ or sale orders from files
[sale_order_import_ubl](sale_order_import_ubl/) | 14.0.1.4.1 |  | Import UBL XML sale order files
[sale_order_import_ubl_customer_free_ref](sale_order_import_ubl_customer_free_ref/) | 14.0.1.1.0 |  | Extract CustomerReference from sale UBL
[sale_order_import_ubl_line_customer_ref](sale_order_import_ubl_line_customer_ref/) | 14.0.1.0.2 |  | Extract specific customer reference for each order line
[sale_order_packaging_import](sale_order_packaging_import/) | 14.0.1.1.0 |  | Import the packaging on the sale order line
[sale_order_ubl](sale_order_ubl/) | 14.0.1.1.1 |  | Embed UBL XML file inside the PDF quotation

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
