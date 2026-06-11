This module adds a button *Import Quotation File* on Requests for Quotation. This button starts a wizard that will propose you to select the quotation file. The wizard will also propose you an update option:

* only update the prices of the draft purchase order from the quotation file (default option),
* update prices and quantities of the draft purchase order from the quotation file.

When you click on the button *Update RFQ*:

* if Odoo has a line in the quotation file that is not in the draft purchase order, it will create a new purchase order line,
* if Odoo has a line in the draft purchase order that is not in the quotation file, it will write a warning in the chatter of the purchase order (it will not delete the purchase order line),
* for all the lines that are both in the draft purchase order and in the quotation file, the purchase order line will be updated if needed.
* if the incoterm of the quotation file is not the same as the incoterm of the draft purchase order, Odoo will update the incoterm of the purchase order.
* the imported quotation file is attached to the purchase order.

Once the quotation file is imported, you should read the messages in the chatter of the purchase order because it may contain important information about the import.
