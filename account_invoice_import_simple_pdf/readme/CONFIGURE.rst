By default, for the PDF to text conversion, the module tries the different methods in the order mentionned in the INSTALL section: it will first try to use **PyMuPDF**; if it fails (for example because the lib is not properly installed), then it will try to use the **pdftotext python lib**, if that one also fails, it will try to use **pdftotext command line** and, if it also fails, it will eventually try **pdfplumber**. If none of the 4 methods work, Odoo will display an error message.

If you want to force Odoo to use a specific text extraction method, go to the menu *Configuration > Technical > Parameters > System Parameters* and create a new System Parameter:

* *Key*: **invoice_import_simple_pdf.pdf2txt**
* *Value*: select the proper value for the method you want to use:

  1. pymupdf
  #. pdftotext.lib
  #. pdftotext.cmd
  #. pdfplumber

In this configuration, Odoo will only use the selected text extraction method and, if it fails, it will display an error message.

You will find a full demonstration about how to configure each Vendor and import the PDF invoices in this `screencast <https://www.youtube.com/watch?v=edsEuXVyEYE>`_.
