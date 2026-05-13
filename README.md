
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/edi/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/edi/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/edi/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/edi/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/edi/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/edi)
[![Translation Status](https://translation.odoo-community.org/widgets/edi-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/edi-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# edi

---

EDI (Electronic Data Interchange) is the exchange of business documents in a standardized electronic format between companies.

It replaces manual and paper-based document exchange with automated data processing, commonly used in B2B workflows, especially where large volumes of documents are exchanged. It can also be used by smaller companies.

More information:  
https://en.wikipedia.org/wiki/Electronic_data_interchange

**Use in various industries:**  
retail/e-commerce, logistics, automotive, healthcare, finance, distribution, manufacturing, public sector (e-invoicing).

---

## ⭐ EDI Features

- Automation of business processes  
- Digitalization of documents  
- Exchange of business documents (orders, invoices, delivery notes, order confirmations, shipping notices / advanced shipping notices,  
  receiving advice / acceptance certificates, etc.).  
  Note: document names may vary depending on the standard used.
- Transformation, parsing, and mapping of data between systems  
- unification of document formats and standards (XML, cXML, JSON, IDoc, EDIFACT, ANSI X12, UBL, etc.).

---

## ⚙️ How it works

EDI can be used as an application, but more commonly it is integrated into an ERP system (e.g. Odoo ERP EDI) or ERP middleware (e.g. SAP CPI, Seeburger).

For a standard installation, please follow the setup instructions:  
https://www.odoo.com/documentation/master/administration/on_premise.html
https://www.odoo.com/

To learn the software, we recommend Odoo eLearning or Scale-up (business game). Developers can start with developer tutorials.

Business partners agree on:
- a standard (EDIFACT / ANSI X12 / UBL)  
- transport method (AS2 / HTTP/HTTPS, SFTP, VAN, API, email, EDI broker)

→ automation is then configured in ERP systems (Odoo, SAP-OCI, Infor, etc.).

*(This does not mean that a company located in Europe must necessarily use EDIFACT).*

---

## 🧩 Requirements

Requires an Odoo Community environment (Python + PostgreSQL).

Works on any OS supporting Python + PostgreSQL (Linux/macOS/Windows), recommended via Docker or WSL.

For development/testing:
- Docker (easiest way)
- Odoo Community source (GitHub install)
- addons path config

---

## 📦 Standards / Formats

  Common EDI standards are managed by UN/CEFACT and ANSI X12:

- EU EDIFACT: https://unece.org/trade/uncefact/introducing-unedifact  
- US ANSI X12: https://x12.org  
- UBL (Universal Business Language = XML + XSD schema): https://www.w3.org/XML/Schema , https://www.oasis-open.org/ubl

---

## 🧱 Module structure

This repository contains a collection of modules (usually 1 folder = 1 module) for Odoo that handle Electronic Data Interchange (EDI) processes such as document generation, parsing, and data transformation.

Modules are organized by role in the EDI workflow:

**📤 Export modules**
- Generate EDI documents from Odoo business data (e.g. invoices, orders)

**📥 Import modules**
- Parse and validate incoming EDI documents into Odoo models

**🔧 Base modules**
- Provide shared logic, models, and helpers used across EDI workflows

Each module is a standard Odoo addon (with its own `__manifest__.py`) and typically focuses on a specific part of the EDI process, such as transforming business data into structured formats (e.g. UBL, EDIFACT, ANSI X12) or importing external documents into Odoo.

This section describes common patterns across modules rather than listing them individually, as modules are continuously added and extended.

---

## 🔗 Related repository

Shared EDI base framework logic are maintained in:

https://github.com/OCA/edi-framework

Odoo module framework provides a unified interface for automated document exchange (invoices, orders, delivery notes, etc.) between Odoo and other systems (e.g. public administration, business partners).

- Structured data is transmitted in standardized formats ensuring compatibility  
- Flexibility allows integration of different formats and protocols  

EDI framework = foundation (technical layer)  
This repository = real use-case modules built on top of it  

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_einvoice_generate](account_einvoice_generate/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Technical module to generate PDF invoices with embedded XML file
[account_invoice_download](account_invoice_download/) | 18.0.1.1.1 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Auto-download supplier invoices and import them
[account_invoice_download_ovh](account_invoice_download_ovh/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Get OVH Invoice via the API
[account_invoice_download_scaleway](account_invoice_download_scaleway/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Get Scaleway Invoices via the API
[account_invoice_export](account_invoice_export/) | 18.0.1.0.1 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Account Invoice Export
[account_invoice_export_job](account_invoice_export_job/) | 18.0.1.0.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Account Invoice Export Job
[account_invoice_export_server_env](account_invoice_export_server_env/) | 18.0.1.0.0 |  | Server environment for Account Invoice Export
[account_invoice_facturx](account_invoice_facturx/) | 18.0.2.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Generate Factur-X/ZUGFeRD customer invoices
[account_invoice_facturx_py3o](account_invoice_facturx_py3o/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Generate Factur-X invoices with Py3o reporting engine
[account_invoice_import](account_invoice_import/) | 18.0.1.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import supplier invoices/refunds as PDF or XML files
[account_invoice_import_facturx](account_invoice_import_facturx/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import Factur-X/ZUGFeRD Vendor Bills
[account_invoice_import_simple_pdf](account_invoice_import_simple_pdf/) | 18.0.1.1.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import simple PDF vendor bills
[account_invoice_import_ubl](account_invoice_import_ubl/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Import UBL XML supplier invoices/refunds
[base_business_document_import](base_business_document_import/) | 18.0.2.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Provides technical tools to import sale orders or supplier invoices
[base_business_document_import_phone](base_business_document_import_phone/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Use phone numbers to match partners upon import of business documents
[base_ebill_payment_contract](base_ebill_payment_contract/) | 18.0.1.0.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Base for managing e-billing contracts
[base_edi](base_edi/) | 18.0.1.0.2 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Base module to aggregate EDI features.
[base_facturx](base_facturx/) | 18.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Base module for Factur-X/ZUGFeRD
[base_import_pdf_by_template](base_import_pdf_by_template/) | 18.0.1.0.1 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Base Import Pdf by Template
[base_import_pdf_by_template_account](base_import_pdf_by_template_account/) | 18.0.1.0.1 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Base Import Pdf by Template Account
[base_ubl](base_ubl/) | 18.0.1.0.0 |  | Base module for Universal Business Language (UBL)
[base_ubl_generate](base_ubl_generate/) | 18.0.1.0.0 |  | Base module to generate UBL files (Universal Business Language)
[base_ubl_parse](base_ubl_parse/) | 18.0.1.0.0 |  | Base module to parse UBL files (Universal Business Language)
[partner_identification_import](partner_identification_import/) | 18.0.1.0.0 |  | Provides partner matching on extra ID
[sale_order_customer_free_ref](sale_order_customer_free_ref/) | 18.0.1.0.0 |  | Splits the Customer Reference on sale orders into two fields. An Id and a Free reference. The existing field is transformed into a computed one.
[sale_order_import](sale_order_import/) | 18.0.1.1.0 |  | Import RFQ or sale orders from files
[sale_order_import_packaging](sale_order_import_packaging/) | 18.0.1.0.0 |  | Import the packaging on the sale order line
[sale_order_import_ubl](sale_order_import_ubl/) | 18.0.1.0.1 |  | Import UBL XML sale order files
[sale_order_import_ubl_customer_free_ref](sale_order_import_ubl_customer_free_ref/) | 18.0.1.0.0 |  | Extract CustomerReference from sale UBL
[sale_order_import_ubl_line_customer_ref](sale_order_import_ubl_line_customer_ref/) | 18.0.1.0.0 |  | Extract specific customer reference for each order line
[sale_order_import_ubl_requested_delivery](sale_order_import_ubl_requested_delivery/) | 18.0.1.0.0 |  | Extract RequestedDeliveryPeriod from sale UBL

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
