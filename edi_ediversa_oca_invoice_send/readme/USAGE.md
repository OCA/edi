The generation/delivery flow of the Ediversa invoices files is as follows:
- When an invoice is validated, a job to generate the Ediversa invoice file is created.
- The scheduled action "EDI exchange check output sync" sends the invoice file to
  Ediversa.
