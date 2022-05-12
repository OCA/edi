This module requires the Python library *invoice2data* available on `Github <https://github.com/invoice-x/invoice2data>`_ with a version >= 0.2.74 (February 2018).

To install the latest version of this library, run:

.. code::

  sudo pip3 install --upgrade invoice2data

If you use Ubuntu 16.04 LTS or higher, you can use the pdftotext version 0.41.0 that is packaged in the distribution:

.. code::

  sudo apt install poppler-utils

If you want the invoice2data library to support mixed-type pdf's or fallback on OCR if the PDF doesn't contain text (only a very small minority of PDF invoices are image-based and require OCR) like scanned receipts, you should also install `Ocrmypdf <https://github.com/ocrmypdf/OCRmyPDF>`_

.. code::

  pip install -U ocrmypdf

If you want the invoice2data library to fallback on OCR if the PDF doesn't contain text (only a very small minority of PDF invoices are image-based and require OCR) like scanned receipts, you should also install `Imagemagick <https://www.imagemagick.org/>`_ (to get the *convert* utility to convert PDF to TIFF) and `Tesseract OCR <https://github.com/tesseract-ocr/tesseract>`_ :

.. code::

  sudo apt install imagemagick tesseract-ocr

If you want to use custom invoice templates for the invoice2data lib (in addition to the templates provided by the invoice2data lib), you should add a line in your Odoo server configuration file such as:

.. code::

  invoice2data_templates_dir = /opt/invoice2data_local_templates

and store your invoice templates in YAML format (*.yml* extension) or json format in the directory that you have configured above. If you add invoice tempates in this directory, you don't have to restart Odoo, they will be used automatically on the next invoice import.

If you want to use only your custom invoice templates and ignore the templates provided by the invoice2data lib, you should have in your Odoo server configuration file:

.. code::

  invoice2data_templates_dir = /opt/invoice2data_local_templates
  invoice2data_exclude_built_in_templates = True

The yaml templates are loaded with [pyyaml](https://github.com/yaml/pyyaml) which is a pure python implementation. (thus rather slow)
As an alternative json templates can be used. Which are natively better supported by python. The performance with yaml templates can be greatly increased **10x** by using [libyaml](https://github.com/yaml/libyaml)
It can be installed on most distributions by:

.. code::

  sudo apt-get libyaml-dev

French users should also install the module *l10n_fr_business_document_import* available in the `French localization <https://github.com/OCA/l10n-france/>`_.
Dutch users should also install the module *l10n_nl_business_document_import* available in the `Netherlands localization <https://github.com/OCA/l10n-netherlands/>`_.

Dependencies
============
| Name | Requirement | Installation | Description |
| -------------- | :---------: | :---------: | :-------------------------------------- |
| [invoice2data](https://github.com/invoice-x/invoice2data) | required | `pip install invoice2data` | The main dependency of this invoice import module |
| [poppler-utils](https://poppler.freedesktop.org/) | required | `apt install poppler-utils` | The default Input-reader for the invoice2data library |
| [dateparser](https://dateparser.readthedocs.io/en/latest/#) | required | `pip install dateparser` | Requirement for parsing the invoice dates, this requirement is likely already satisfied by odoo itself |
| [libyaml](https://github.com/yaml/libyaml) | optional | `apt install libyaml-dev` | Template loader, recomended to greatly speedup the loading of yaml templates |
| [imagemagick](https://www.imagemagick.org) | optional | `apt install imagemagick` | inputreader: Pre-processes the pdf before feeding it into tesseract-ocr |
| [tesseract-ocr](https://github.com/tesseract-ocr/tesseract) | optional | `apt install tesseract-ocr` | inputreader: for ocr of image only pdf files |
| [tesseract-ocr- lang](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html) | optional | `apt install tesseract-ocr-` see documentation | inputreader: Language pack for tesseract ocr, greatly improves character detection |
| [ocrmypdf](https://github.com/ocrmypdf/OCRmyPDF) | optional | `apt install ocrmypdf` | inputreader: For image only or mixed type pdf's. It uses tesseract-ocr under the hood, but provides optimalisations which greatly improves results |
