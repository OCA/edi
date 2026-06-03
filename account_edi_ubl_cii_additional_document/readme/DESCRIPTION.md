This module extends `account_edi_ubl_cii` to import all attachments included
in UBL invoices, not only PDF files.

During the import process, additional documents provided by the supplier
(e.g. XLSX, CSV, images) are extracted from the UBL payload and linked to
the generated vendor bill.
