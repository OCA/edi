This module is an extension of the module *account_invoice_import*: it adds support for regular PDF invoices i.e. PDF invoice that don't have an embedded XML file. It uses the `invoice2data library <https://github.com/invoice-x/invoice2data>`_ which takes care of extracting the text of the PDF invoice, find an existing invoice template and execute the invoice template to extract the useful information from the invoice.

To know the full story behind the development of this module, read this `blog post <http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community>`_.

More information for creating the templates can be found in `tutorial of the invoice2data library <https://github.com/invoice-x/invoice2data/blob/master/TUTORIAL.md>`_. The templates have to be created manually. An graphical template creator for odoo is a work in progress.

**WARNING**: an alternative module **account_invoice_import_simple_pdf** developped in July 2021 provides similar features but has one big advantage: the accountant can add support for a new vendor by himself, no more invoice templates which require technical skill. The module *account_invoice_import_simple_pdf* provides basic functionality, but does not support line level accounting.
