This addon prevents to embed a factur-x attachment inside every invoice pdf
by deleting the definition of factur-x as edi format.

See https://github.com/odoo/odoo/blob/9fd78da68bc6167c99932fbc5ec7b1d8e264d5ea/addons/account_edi_ubl_cii/models/ir_actions_report.py#L116

Note that you won't be able to generate a factur-x xml anymore if necessary.
When uninstalling this module, update account_edi_ubl_cii to load back the
factur-x edi format.
