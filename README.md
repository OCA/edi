
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=15.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=15.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A15.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=15.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A15.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/15.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-15-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-15-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# edi

TODO: add repo description.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_einvoice_generate](account_einvoice_generate/) | 15.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Technical module to generate PDF invoices with embedded XML file
[account_invoice_facturx](account_invoice_facturx/) | 15.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X/ZUGFeRD customer invoices
[base_edi](base_edi/) | 15.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 15.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 15.0.1.0.1 |  | Base module for Universal Business Language (UBL)
[edi_account_oca](edi_account_oca/) | 15.0.1.0.1 | [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Define EDI Configuration for Account Moves
[edi_backend_partner_oca](edi_backend_partner_oca/) | 15.0.1.0.0 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | Add the a partner field to EDI backend
[edi_exchange_template_oca](edi_exchange_template_oca/) | 15.0.1.1.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allows definition of exchanges via templates.
[edi_oca](edi_oca/) | 15.0.1.6.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_stock_oca](edi_stock_oca/) | 15.0.1.0.0 |  | Define EDI Configuration for Stock
[edi_storage_oca](edi_storage_oca/) | 15.0.1.3.0 |  | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_voxel_account_invoice_oca](edi_voxel_account_invoice_oca/) | 15.0.1.0.2 |  | Sends account invoices to Voxel.
[edi_voxel_oca](edi_voxel_oca/) | 15.0.1.0.0 |  | Base module for connecting with Voxel
[edi_voxel_sale_order_import_oca](edi_voxel_sale_order_import_oca/) | 15.0.1.0.1 |  | Import sale order from Voxel.
[edi_voxel_sale_secondary_unit_oca](edi_voxel_sale_secondary_unit_oca/) | 15.0.1.0.0 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Map Voxel UoM to Sale Secondary UoM and Use Them
[edi_voxel_secondary_unit_oca](edi_voxel_secondary_unit_oca/) | 15.0.1.0.0 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Add Voxel UoM code to Secondary UoM model
[edi_voxel_stock_picking_oca](edi_voxel_stock_picking_oca/) | 15.0.1.0.2 |  | Sends stock picking report to Voxel.
[edi_voxel_stock_picking_secondary_unit_oca](edi_voxel_stock_picking_secondary_unit_oca/) | 15.0.1.0.0 | [![ernestotejeda](https://github.com/ernestotejeda.png?size=30px)](https://github.com/ernestotejeda) | Export Secondary UoMs Voxel Code in picking Voxel documents
[edi_webservice_oca](edi_webservice_oca/) | 15.0.1.2.2 | [![etobella](https://github.com/etobella.png?size=30px)](https://github.com/etobella) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Defines webservice integration from EDI Exchange records
[pdf_helper](pdf_helper/) | 15.0.1.0.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides helpers to work w/ PDFs

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
