In the standard behavior of `account_edi_ubl_cii`, only PDF attachments from
UBL invoices are imported and linked to the vendor bill.

However, suppliers may include additional documents (e.g. XLSX, CSV, images)
in the UBL payload that are relevant for accounting or reconciliation.

These attachments are currently ignored, creating a need to make all provided
documents available in Odoo.