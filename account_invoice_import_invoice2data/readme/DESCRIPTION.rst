This module is an extension of the module *account_invoice_import*: it adds support for regular PDF invoices i.e. PDF invoice that don't have an embedded XML file. It uses the `invoice2data library <https://github.com/invoice-x/invoice2data>`_ which takes care of extracting the text of the PDF invoice, find an existing invoice template and execute the invoice template to extract the useful information from the invoice.

To know the full story behind the development of this module, read this `blog post <http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community>`_.
