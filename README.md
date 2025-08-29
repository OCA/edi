
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
[account_einvoice_generate](account_einvoice_generate/) | 15.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Technical module to generate PDF invoices with embedded XML file
[account_invoice_facturx](account_invoice_facturx/) | 15.0.1.0.1 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Generate Factur-X/ZUGFeRD customer invoices
[base_edi](base_edi/) | 15.0.1.1.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 15.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Base module for Factur-X/ZUGFeRD
[base_import_pdf_by_template](base_import_pdf_by_template/) | 15.0.1.2.1 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Base Import Pdf by Template
[base_ubl](base_ubl/) | 15.0.1.0.1 |  | Base module for Universal Business Language (UBL)
[edi_account_oca](edi_account_oca/) | 15.0.1.0.1 | <a href='https://github.com/etobella'><img src='https://github.com/etobella.png' width='32' height='32' style='border-radius:50%;' alt='etobella'/></a> | Define EDI Configuration for Account Moves
[edi_backend_partner_oca](edi_backend_partner_oca/) | 15.0.1.0.0 | <a href='https://github.com/LoisRForgeFlow'><img src='https://github.com/LoisRForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='LoisRForgeFlow'/></a> | Add the a partner field to EDI backend
[edi_exchange_template_oca](edi_exchange_template_oca/) | 15.0.1.1.1 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Allows definition of exchanges via templates.
[edi_oca](edi_oca/) | 15.0.1.7.5 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/etobella'><img src='https://github.com/etobella.png' width='32' height='32' style='border-radius:50%;' alt='etobella'/></a> | Define backends, exchange types, exchange records, basic automation and views for handling EDI exchanges.
[edi_stock_oca](edi_stock_oca/) | 15.0.1.0.0 |  | Define EDI Configuration for Stock
[edi_storage_oca](edi_storage_oca/) | 15.0.1.3.0 |  | Base module to allow exchanging files via storage backend (eg: SFTP).
[edi_voxel_account_invoice_oca](edi_voxel_account_invoice_oca/) | 15.0.1.0.4 |  | Sends account invoices to Voxel.
[edi_voxel_oca](edi_voxel_oca/) | 15.0.1.0.1 |  | Base module for connecting with Voxel
[edi_voxel_sale_order_import_oca](edi_voxel_sale_order_import_oca/) | 15.0.1.0.1 |  | Import sale order from Voxel.
[edi_voxel_sale_secondary_unit_oca](edi_voxel_sale_secondary_unit_oca/) | 15.0.1.0.0 | <a href='https://github.com/ernestotejeda'><img src='https://github.com/ernestotejeda.png' width='32' height='32' style='border-radius:50%;' alt='ernestotejeda'/></a> | Map Voxel UoM to Sale Secondary UoM and Use Them
[edi_voxel_secondary_unit_oca](edi_voxel_secondary_unit_oca/) | 15.0.1.0.0 | <a href='https://github.com/ernestotejeda'><img src='https://github.com/ernestotejeda.png' width='32' height='32' style='border-radius:50%;' alt='ernestotejeda'/></a> | Add Voxel UoM code to Secondary UoM model
[edi_voxel_stock_picking_oca](edi_voxel_stock_picking_oca/) | 15.0.1.1.2 |  | Sends stock picking report to Voxel.
[edi_voxel_stock_picking_secondary_unit_oca](edi_voxel_stock_picking_secondary_unit_oca/) | 15.0.1.0.0 | <a href='https://github.com/ernestotejeda'><img src='https://github.com/ernestotejeda.png' width='32' height='32' style='border-radius:50%;' alt='ernestotejeda'/></a> | Export Secondary UoMs Voxel Code in picking Voxel documents
[edi_webservice_oca](edi_webservice_oca/) | 15.0.1.2.2 | <a href='https://github.com/etobella'><img src='https://github.com/etobella.png' width='32' height='32' style='border-radius:50%;' alt='etobella'/></a> <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Defines webservice integration from EDI Exchange records
[pdf_helper](pdf_helper/) | 15.0.1.0.1 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Provides helpers to work w/ PDFs
[test_base_import_pdf_by_template](test_base_import_pdf_by_template/) | 15.0.1.1.1 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Test Base Import Pdf by Template

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
