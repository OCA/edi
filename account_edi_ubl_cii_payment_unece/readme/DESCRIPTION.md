Integrate UNECE Payment Means (module `account_payment_unece` from
[OCA/community-data-files project](https://github.com/OCA/community-data-files/))
with Odoo standard UBL/CII electronic invoices (module `account_edi_ubl_cii`).

When receiving an invoice declared with a payment means SEPA direct debit,
you can configure an outbound payment means with that UNECE code and the created
invoice will have that payment means set so that you know you don't have to pay it.
