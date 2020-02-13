This module requires the Python library *invoice2data* available on `Github <https://github.com/invoice-x/invoice2data>`_ with a version >= 0.2.74 (February 2018).

To install the latest version of this library, run:

.. code::

  sudo pip3 install --upgrade invoice2data

If you use Ubuntu 16.04 LTS or higher, you can use the pdftotext version 0.41.0 that is packaged in the distribution:

.. code::

  sudo apt install poppler-utils

If you want the invoice2data library to fallback on OCR if the PDF doesn't contain text (only a very small minority of PDF invoices are image-based and require OCR), you should also install `Imagemagick <http://www.imagemagick.org/>`_ (to get the *convert* utility to convert PDF to TIFF) and `Tesseract OCR <https://github.com/tesseract-ocr/tesseract>`_ :

.. code::

  sudo apt install imagemagick tesseract-ocr

If you want to use custom invoice templates for the invoice2data lib (in addition to the templates provided by the invoice2data lib), you should add a line in your Odoo server configuration file such as:

.. code::

  invoice2data_templates_dir = /opt/invoice2data_local_templates

and store your invoice templates in YAML format (*.yml* extension) in the directory that you have configured above. If you add invoice tempates in this directory, you don't have to restart Odoo, they will be used automatically on the next invoice import.

If you want to use only your custom invoice templates and ignore the templates provided by the invoice2data lib, you should have in your Odoo server configuration file:

.. code::

  invoice2data_templates_dir = /opt/invoice2data_local_templates
  invoice2data_exclude_built_in_templates = True

French users should also install the module *l10n_fr_business_document_import* available in the `French localization <https://github.com/OCA/l10n-france/>`_.
