[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/226/14.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-edi-226)
[![Build Status](https://travis-ci.com/OCA/edi.svg?branch=14.0)](https://travis-ci.com/OCA/edi)
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
[account_invoice_download](account_invoice_download/) | 14.0.1.0.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Auto-download supplier invoices and import them
[account_invoice_download_ovh](account_invoice_download_ovh/) | 14.0.1.0.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Get OVH Invoice via the API
[account_invoice_export](account_invoice_export/) | 14.0.1.2.0 |  | Account Invoice Export
[account_invoice_export_server_env](account_invoice_export_server_env/) | 14.0.1.0.0 |  | Server environment for Account Invoice Export
[account_invoice_facturx](account_invoice_facturx/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_import](account_invoice_import/) | 14.0.1.1.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import supplier invoices/refunds as PDF or XML files
[account_invoice_import_facturx](account_invoice_import_facturx/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import Factur-X/ZUGFeRD supplier invoices/refunds
[account_invoice_import_invoice2data](account_invoice_import_invoice2data/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import supplier invoices using the invoice2data lib
[account_invoice_import_simple_pdf](account_invoice_import_simple_pdf/) | 14.0.1.0.1 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Import simple PDF vendor bills
[account_invoice_import_ubl](account_invoice_import_ubl/) | 14.0.1.0.1 |  | Import UBL XML supplier invoices/refunds
[account_invoice_ubl](account_invoice_ubl/) | 14.0.1.0.0 |  | Generate UBL XML file for customer invoices/refunds
[base_business_document_import](base_business_document_import/) | 14.0.2.2.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Use phone numbers to match partners upon import of business documents
[base_ebill_payment_contract](base_ebill_payment_contract/) | 14.0.1.0.0 |  | Base for managing e-billing contracts
[base_edi](base_edi/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 14.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 14.0.1.5.1 |  | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 14.0.1.0.0 |  | Payment-related code for Universal Business Language (UBL)
[edi_account_oca](edi_account_oca/) | 14.0.1.1.0 |  | Define EDI Configuration for Account Moves
[edi_backend_partner_oca](edi_backend_partner_oca/) | 14.0.1.0.1 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | add the a partner field in EDI backend
[edi_endpoint_oca](edi_endpoint_oca/) | 14.0.1.2.2 |  | Base module allowing configuration of custom endpoints for EDI framework.
[edi_exchange_template_oca](edi_exchange_template_oca/) | 14.0.1.0.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allows definition of exchanges via templates.
[edi_oca](edi_oca/) | 14.0.1.7.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_sale_order_import](edi_sale_order_import/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Plug sale_order_import into EDI machinery.
[edi_sale_order_import_ubl](edi_sale_order_import_ubl/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Plug sale_order_import_ubl into EDI machinery.
[edi_sale_order_import_ubl_endpoint](edi_sale_order_import_ubl_endpoint/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Provide a default endpoint to import SO in UBL format.
[edi_storage_oca](edi_storage_oca/) | 14.0.1.4.0 |  | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_ubl_oca](edi_ubl_oca/) | 14.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Define EDI backend type for UBL.
[edi_webservice_oca](edi_webservice_oca/) | 14.0.1.1.0 |  | Defines webservice integration from EDI Exchange records
[endpoint](endpoint/) | 14.0.1.1.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Provide custom endpoint machinery.
[endpoint_auth_api_key](endpoint_auth_api_key/) | 14.0.1.1.2 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Provide API key auth for endpoints.
[endpoint_route_handler](endpoint_route_handler/) | 14.0.1.0.4 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Provide mixin and tool to generate custom endpoints on the fly.
[partner_identification_import](partner_identification_import/) | 14.0.1.0.1 |  | Provides partner matching on extra ID
[purchase_order_ubl](purchase_order_ubl/) | 14.0.1.0.0 |  | Embed UBL XML file inside the PDF purchase order
[sale_order_customer_free_ref](sale_order_customer_free_ref/) | 14.0.1.0.0 |  | Splits the Customer Reference on sale orders into two fields. An Id and a Free reference. The existing field is transformed into a computed one.
[sale_order_import](sale_order_import/) | 14.0.1.2.2 |  | Import RFQ or sale orders from files
[sale_order_import_ubl](sale_order_import_ubl/) | 14.0.1.2.0 |  | Import UBL XML sale order files
[sale_order_import_ubl_customer_free_ref](sale_order_import_ubl_customer_free_ref/) | 14.0.1.1.0 |  | Extract CustomerReference from sale UBL
[sale_order_ubl](sale_order_ubl/) | 14.0.1.0.0 |  | Embed UBL XML file inside the PDF quotation
[webservice](webservice/) | 14.0.1.0.1 |  | Defines webservice abstract definition to be used generally

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
