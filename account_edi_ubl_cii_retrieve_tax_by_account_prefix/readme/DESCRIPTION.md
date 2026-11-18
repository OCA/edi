This module is a glue module between `account_invoice_tax_allowed_account_prefix`
and `account_edi_ubl_cii_retrieve_tax`.

It extends the UBL import process to take into account the account prefix
restriction when retrieving taxes, ensuring that only taxes compatible with
the invoice line account are selected.
