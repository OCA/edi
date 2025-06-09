This module adds a wizard in the sale menu named *Import RFQ or Order*. This wizard will propose you to select the order or RFQ file. Depending on the format of the file (XML or PDF) and the type of file (RFQ or order), it may propose you additional options.

When you import an order, if there is a quotation in Odoo for the same customer, the wizard will propose you to either update the existing quotation or create a new order (in fact, it will create a new quotation, so that you are free to make some modifications before you click on the *Confirm Sale* button to convert the quotation to a sale order).

Once the RFQ/order is imported, you should read the messages in the chatter of the quotation because it may contain important information about the import.
