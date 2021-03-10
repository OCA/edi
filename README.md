[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/226/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-edi-226)
[![Build Status](https://travis-ci.com/OCA/edi.svg?branch=13.0)](https://travis-ci.com/OCA/edi)
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
addon | version | summary
--- | --- | ---
[account_e-invoice_generate](account_e-invoice_generate/) | 13.0.1.0.0 | Technical module to generate PDF invoices with embedded XML file
[account_invoice_export](account_invoice_export/) | 13.0.1.0.0 | Account Invoice Export
[account_invoice_facturx](account_invoice_facturx/) | 13.0.1.0.0 | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 13.0.1.0.0 | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_ubl](account_invoice_ubl/) | 13.0.1.0.4 | Generate UBL XML file for customer invoices/refunds
[account_invoice_ubl_email_attachment](account_invoice_ubl_email_attachment/) | 13.0.1.1.0 | Automatically adds the UBL file to the email.
[base_business_document_import](base_business_document_import/) | 13.0.2.0.0 | Provides technical tools to import sale orders or supplier invoices
[base_ebill_payment_contract](base_ebill_payment_contract/) | 13.0.1.0.0 | Base for managing e-billing contracts
[base_edi](base_edi/) | 13.0.1.0.0 | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 13.0.1.0.0 | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 13.0.2.0.1 | Base module for Universal Business Language (UBL)
[base_ubl_payment](base_ubl_payment/) | 13.0.1.0.0 | Payment-related code for Universal Business Language (UBL)
[edi](edi/) | 13.0.1.14.1 | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_account](edi_account/) | 13.0.1.0.1 | Define EDI Configuration for Account Moves
[edi_exchange_template](edi_exchange_template/) | 13.0.1.4.0 | Allows definition of exchanges via templates.
[edi_storage](edi_storage/) | 13.0.1.3.0 | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_voxel](edi_voxel/) | 13.0.1.0.0 | Base module for connecting with Voxel
[edi_voxel_account_invoice](edi_voxel_account_invoice/) | 13.0.1.0.1 | Sends account invoices to Voxel.
[edi_voxel_sale_order_import](edi_voxel_sale_order_import/) | 13.0.1.0.0 | Import sale order from Voxel.
[edi_voxel_stock_picking](edi_voxel_stock_picking/) | 13.0.1.0.1 | Sends stock picking report to Voxel.
[edi_xml](edi_xml/) | 13.0.1.1.0 | Base module for EDI exchange using XML files.
[partner_identification_import](partner_identification_import/) | 13.0.2.0.0 | Provides partner matching on extra ID
[purchase_order_ubl](purchase_order_ubl/) | 13.0.1.2.0 | Embed UBL XML file inside the PDF purchase order
[purchase_stock_ubl](purchase_stock_ubl/) | 13.0.1.1.0 | Glue module for Purchase Order UBL and Stock/Inventory
[sale_order_import](sale_order_import/) | 13.0.2.0.0 | Import RFQ or sale orders from files
[sale_order_import_ubl](sale_order_import_ubl/) | 13.0.2.0.0 | Import UBL XML sale order files
[sale_order_ubl](sale_order_ubl/) | 13.0.1.0.0 | Embed UBL XML file inside the PDF quotation

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
