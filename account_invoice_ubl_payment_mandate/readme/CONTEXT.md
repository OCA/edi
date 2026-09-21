Peppol BIS Billing rule PEPPOL-EN16931-R061 requires a mandate reference when
an invoice uses direct debit as payment means.

This module is useful when customer invoices are exported as UBL and paid by
direct debit, especially for SEPA direct debit flows managed with banking
mandates.

The module acts as glue between `account_invoice_ubl`, `base_ubl_payment`, and
`account_banking_mandate`. It reuses the mandate set on the invoice to fill the
UBL `PaymentMandate` information.
