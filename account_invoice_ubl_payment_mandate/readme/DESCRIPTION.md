This module extends the UBL invoice generation to include direct debit mandate
information in the `PaymentMeans` block.

When the invoice payment means code is `49` (Direct debit) or `59` (SEPA direct
debit), the generated UBL XML contains a `PaymentMandate` node with the mandate
reference and the payer bank account.
