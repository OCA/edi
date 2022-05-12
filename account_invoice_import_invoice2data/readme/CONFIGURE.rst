Go to the form view of the supplier and configure it with the following parameters:

* the *VAT* is set (the VAT number is used by default when searching the supplier in the Odoo partner database)
* in the *Invoicing* tab, create an *Invoice Import Configuration*.

For the PDF invoice of your supplier that don't have an embedded XML file, you will have to create a `template file <https://github.com/invoice-x/invoice2data/tree/master/src/invoice2data/extract/templates>`_ in YAML format in the invoice2data Python library. It is quite easy to do ; if you are familiar with `regexp <https://docs.python.org/3/library/re.html>`_, it should not take more than 10 minutes for each supplier.

Here are some hints to help you add a template for your supplier:

* There is a `tutorial in the repo of the invoice2data library <https://github.com/invoice-x/invoice2data/blob/master/TUTORIAL.md>`_

* Take `Free SAS template file <https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/templates/fr/fr.free.adsl-fiber.yml>`_ as an example. You will find a sample PDF invoice for this supplier under invoice2data/test/pdf/invoice_free_fiber_201507.pdf

* Try to run the invoice2data library manually on the sample invoice of Free:

.. code::

  % python -m invoice2data.main --debug invoice2data/test/pdf/invoice_free_fiber_201507.pdf

On the output, you will get first the text of the PDF, then some debug info on the parsing of the invoice and the regexps, and, on the last line, you will have the dict that contain the result of the parsing.

* if the VAT number of the supplier is present in the text of the PDF invoice, I think it's a good idea to use it as the keyword. It is good practice to add 2 other keywords: one for the language (for example, match on the word *Invoice* in the language of the invoice) and one for the currency, to match only the invoices of that supplier in this particular language and currency.

* the list of *fields* should contain the following entries:

  * 'vat' with the VAT number of the supplier (if the VAT number of the supplier is not in the text of PDF file, add a 'partner_name' key)
  * 'amount' ('amount' is the total amount with taxes)
  * 'amount_untaxed' or 'amount_tax' (one or the other, no need for both)
  * 'date': the date of the invoice
  * 'invoice_number'
  * 'date_due', if this information is available in the text of the PDF file.

The invoice2data library is quite powerfull. It supports multiple input methods (pdftotext, ocrmypdf, tesseract ocr, google cloud vision).
Even invoicelines can be imported and mapped to products in the database.
The invoice2data library does not have a strict standard on field names. This makes the module very flexible, but also hard to create re-usable templates.

If you want to make use of the advanced features, support for the following fields is implemented.

## Supported fields

(note: the fieldname column contains the name to be used in the template file.)

Partner fields
| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| vat | char | The vat code is unique for each partner, it has the highest priority for matching the partner  |
| partner_name | char | self explaining |
| partner_street | char | self explaining |
| partner_street2 | char | self explaining |
| partner_street3 | char | self explaining |
| partner_city | char | self explaining |
| partner_zip | char | self explaining |
| country_code | char | use iso format fr or nl |
| state_code | char | use iso format NY (for New York) |
| partner_email | char | self explaining |
| partner_website | char | self explaining |
| telephone | char | can be used for matching the partner with the help of support modules  |
| mobile | char | can be used for matching the partner contact with the help of support modules  |
| partner_ref | char | reference name or number can be used for partner matching |
| siren | char | French business code, can be used for matching the partner |
| partner_coc | char | General business identiefier number, can be used for matching the partner |

Invoice Fields (on document level)
| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| currency | char | The currency of the invoice in iso format (EUR, USD) |
| currency_symbol | char | The currency symbol of the invoice (€, $) |
| bic | char | Bank Identifier Code |
| iban | char | International Bank Account Number |
| amount | float | The total amount of the invoice (including taxes) |
| amount_untaxed | float | The total amount of the invoice (excluding taxes) |
| amount_tax | float | The sum of the tax amount of the invoice |
| date | date | The date of the invoice |
| invoice_number | char | self explaining |
| date_due | date | The duedate of the invoice |
| date_start | date | The start date of the period for the invoice when the services are delivered. |
| date_end | date | The start date of the period for the invoice when the services are delivered. |
| note | char | The contents of this field will be imported in the chatter. |
| narration | char | The contents of this field will be imported in the narration field. (on the bottom of the invoice.) |
| payment_reference | char | If the invoice is pre-paid an reference can be used for payment reconciliation |
| payment_unece_code | char | The unece code of the payment means according to 4461 code list |
| incoterm | char | The Incoterm 2000 abbrevation |
| company_vat | char | The vat number of the company to which the invoice is addressed to. Used to check if the invoice is actually is adressed to the company which wants to process it. (Very useful in multi-company setup) |
| mandate_id | char | A banking mandate is attached to a bank account and represents an authorization that the bank account owner gives to a company for a specific operation (such as direct debit). |


Invoice line Fields
| fieldname | type | Description |
| -------------- | :---------: | :-------------------------------------- |
| name | char | The name of the product, can be used for product matching |
| barcode | char | The the barcode of the product or product package, used for product matching |
| code | char | The (internal) product code, used for product matching |
| qty | float | The amount of items/units |
| unece_code | char | The unece code of the products units of measure can be passed |
| uom | char | The name of the unit of measure, internally if will be mapped to the unece code. Example L will be mapped to unece_code LTR |
| price_unit | float | The unit price of the item. (excluding taxes) |
| discount | float | The amount of discount for this line. Eg 20 for 20% discount or 0.0 for no discount |
| price_subtotal | float | The total amount of the invoice line excluding taxes. It can be used to create adjustment lines when the decimal precision is insufficient. |
| line_tax_percent | float | The percentage of tax |
| line_tax_amount | float | The fixed amount of tax applied to the line |
| line_note | char | Notes on the invoice can be imported, There is a special view available. |
| sectionheader | char | There is a special view available for section headers. |
| date_start | date | The start date of the period for the invoice when the services are delivered. |
| date_end | date | The start date of the period for the invoice when the services are delivered. |
