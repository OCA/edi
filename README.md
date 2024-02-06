
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-16-0/?utm_source=widget)

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
[account_einvoice_generate](account_einvoice_generate/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Technical module to generate PDF invoices with embedded XML file
[account_invoice_edifact](account_invoice_edifact/) | 16.0.1.0.0 |  | Generate customer invoices with EDIFACT/D96A format
[account_invoice_facturx](account_invoice_facturx/) | 16.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Generate Factur-X invoices with Py3o reporting engine
[base_business_document_import](base_business_document_import/) | 16.0.1.1.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Use phone numbers to match partners upon import of business documents
[base_edi](base_edi/) | 16.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Base module to aggregate EDI features.
[base_edifact](base_edifact/) | 16.0.1.2.0 | [![rmorant](https://github.com/rmorant.png?size=30px)](https://github.com/rmorant) | UN/EDIFACT/D96A utilities using pydifact parser
[base_facturx](base_facturx/) | 16.0.1.0.0 | [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Base module for Factur-X/ZUGFeRD
[base_ubl](base_ubl/) | 16.0.1.1.0 |  | Base module for Universal Business Language (UBL)
[base_wamas_ubl](base_wamas_ubl/) | 16.0.1.6.1 |  | Base module to aggregate WAMAS - UBL features.
[despatch_advice_import](despatch_advice_import/) | 16.0.1.0.0 |  | Despatch Advice import
[despatch_advice_import_ubl](despatch_advice_import_ubl/) | 16.0.1.0.0 |  | Import Despatch Advice files
[pdf_helper](pdf_helper/) | 16.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![alexis-via](https://github.com/alexis-via.png?size=30px)](https://github.com/alexis-via) | Provides helpers to work w/ PDFs
[sale_order_import](sale_order_import/) | 16.0.1.2.0 |  | Import RFQ or sale orders from files
[sale_order_import_edifact](sale_order_import_edifact/) | 16.0.1.0.0 | [![rmorant](https://github.com/rmorant.png?size=30px)](https://github.com/rmorant) | EDIFACT/D96A Order

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
