* Remove dependency on *base_iban* and develop a separate glue module between this module and *base_iban*

* Enhance the update of an existing invoice by analysing the lines (lines are only available when the invoice has an embedded XML file)

* Add a mail gateway to be able to forward the emails that we receive with PDF invoices to a dedicated address ; the gateway would detach the PDF invoice from the email and create the draft supplier invoice in Odoo.
