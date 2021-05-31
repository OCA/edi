Go to the menu *Invoicing > Vendors > Import Vendor Bill* and follow the instructions of the wizard. You can also start the wizard from the *Accounting Dashboard*: on the purchase journal, click on the *Upload* button.

This module also supports the scenario where you have a draft vendor bill (generated from a purchase order for instance) and you have to update it to comply with the real invoice sent by the vendor: on the form view of the draft vendor bill, click on the button *Import Invoice File* and follow the instructions of the wizard.

If you have a large volume of invoices to import, you may be interested by the script **mass_invoice_import.py** which is available in the *scripts* subdirectory of this module. If you run:

.. code::

  ./mass_invoice_import.py --help

you will have detailed instructions on how to use the script.

A particular use case of this script is to have a directory where all the invoices saved are automatically uploaded in Odoo. For that, have a look at the sample script **inotify-sample.sh** available in the same subdirectory. Edit this sample script to adapt it to your needs.
