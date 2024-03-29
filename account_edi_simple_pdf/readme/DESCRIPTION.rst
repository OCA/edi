This module extends Odoo's vendor bill import mechanism with support for simple PDF invoices i.e. PDF invoice that don't have an embedded XML file.

* Possibility to add support for a new vendor without developper skills: the accountant can do it!
* Adding support for a new vendor is faster.
* More tolerance on vendor invoice layout changes.
* Easier to install.

Ihis module uses the following design when importing a PDF vendor bill:

1. raw text extraction of the PDF file,
2. identify the partner using the VAT number (if the VAT number is present in the raw text extraction) or some keywords,
3. use regular expressions (regex) to extract the data needed to create the vendor bill in Odoo (single line configuration).

Under the hood, regular expressions are auto-generated from the configuration made by the user in Odoo. No need to be a regex expert! But you can still write regexes to extract some fields for some very specific needs.

The module can extract the following fields:

* Total Amount with taxes
* Total Untaxed Amount
* Total Tax Amount
* Invoice Date
* Due Date
* Start Date
* End Date
* Invoice Number
* Description (for that field, you have to write a regex)

In this list, only 3 fields are required:

* Invoice Date
* 2 out of the 3 Amount fields (the 3rd can be deducted from the 2 others: Total Amount = Total Untaxed + Total Tax)

To take advantage of the fields *Start Date* and *End Date*, you need the OCA module *account_invoice_start_end_dates* from the `account-closing <https://github.com/OCA/account-closing>`_ project.
