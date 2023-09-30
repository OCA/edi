* Currently, the user needs to configure the PEPPOL EAS id for each country. For the Netherlands, this is for example `0106`, which stands for Dutch chamber of commerce number. During review, it was noted that (defaults for) these codes could be mapped automatically upon installation of the module, using a post-init hook or a noupdate=1 XML file. This could still be done, saving the perhaps not so tech- or PEPPOL-savvy user some configuration.
* Currently, this module defines allowed EAS codes from a CSV file. But, other modules could also benefit from this data. So the data could be moved to a separate module in the `community-data-files` repository.
* When adding a delivery partner to an invoice, some PEPPOL warnings arise about `DeliveryParty` that should not be included. This is non blocking but it is nice if we could also add a clause in the module to remove this.
* A unit test should be added that actually verifies against PEPPOL and not only against general UBL. This could consist of:

   * Choose a default tax and UoM for this module in `res.config.settings`
   * Create an outgoing invoice on the main company to some partner
   * On the main company's partner record, choose any EU country, set a VAT number and a CoC number
   * On the partner record that is being invoiced, do the same.
   * On the `res.country` records that are being used by these partners, configure a valid PEPPOL EAS code.
   * On both involved partners, configure a bank account.
   * The payment mode that is selected on the invoice should have a `fixed` link to a bank journal.
   * On this bank journal, select a bank account of type `IBAN`.
   * Create a tax and selecting a UNECE tax category (eg. VAT) and a tax type (eg. S)
   * The invoice lines should have this tax defined.
   * Validate the invoice, generate the XML, and pass it through the validator.
* This needs to be tested more thoroughly on credit/refund invoices, and purchase invoices.
* Currently, the module fill in the due date under `PaymentTerms`, but we could prefer the Odoo payment terms field if it is filled.
* Upon clicking Print and Send button on invoice, when an error is encountered, the popup will coincide with the `mail.compose` popup. Improve the UI experience to the user here.
