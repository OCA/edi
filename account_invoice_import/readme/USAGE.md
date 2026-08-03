Go to the menu *Invoicing \> Vendors \> Import Vendor Bills* and follow
the instructions of the wizard. You can also start the wizard from the
*Accounting Dashboard*: on the purchase journal, click on the *Upload*
button.

When a vendor cannot be matched automatically, the imported vendor bill
is created without a partner. Use the *Create or Update Partner* button
on the draft vendor bill to create a new partner or update an existing
one from the imported data.

If you have a large volume of invoices to import, you may be interested
by the script **mass_invoice_import.py** which is available in the
*scripts* subdirectory of this module. If you run:

``` 
./mass_invoice_import.py --help
```

you will have detailed instructions on how to use the script.

A particular use case of this script is to have a directory where all
the invoices saved are automatically uploaded in Odoo. For that, have a
look at the sample script **inotify-sample.sh** available in the same
subdirectory. Edit this sample script to adapt it to your needs.
