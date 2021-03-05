Go to the form view of the supplier and configure it with the following parameters:

* the *VAT* is set (the VAT number is used by default when searching the supplier in the Odoo partner database)
* in the *Invoicing* tab, create an *Invoice Import Configuration*.

For the PDF invoice of your supplier that don't have an embedded XML file, you will have to create a `template file <https://github.com/invoice-x/invoice2data/tree/master/src/invoice2data/extract/templates>`_ in YAML format in the invoice2data Python library. It is quite easy to do ; if you are familiar with `regexp <https://docs.python.org/3/library/re.html>`_, it should not take more than 10 minutes for each supplier.

Here are some hints to help you add a template for your supplier:

* Take `Free SAS template file <https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/templates/fr/fr.free.adsl-fiber.yml>`_ as an example. You will find a sample PDF invoice for this supplier under invoice2data/test/pdfs/2015-07-02-invoice_free_fiber.pdf

* Try to run the invoice2data library manually on the sample invoice of Free:

.. code::

  % python -m invoice2data.main --debug invoice2data/test/pdfs/2015-07-02-invoice_free_fiber.pdf

On the output, you will get first the text of the PDF, then some debug info on the parsing of the invoice and the regexps, and, on the last line, you will have the dict that contain the result of the parsing.

* if the VAT number of the supplier is present in the text of the PDF invoice, I think it's a good idea to use it as the keyword. It is a good practice to add 2 other keywoards: one for the language (for example, match on the word *Invoice* in the language of the invoice) and one for the currency, so as to match only the invoices of that supplier in this particular language and currency.

* the list of *fields* should contain the following entries:

  * 'vat' with the VAT number of the supplier (if the VAT number of the supplier is not in the text of PDF file, add a 'partner_name' key)
  * 'amount' ('amount' is the total amount with taxes)
  * 'amount_untaxed' or 'amount_tax' (one or the other, no need for both)
  * 'date': the date of the invoice
  * 'invoice_number'
  * 'date_due', if this information is available in the text of the PDF file.
