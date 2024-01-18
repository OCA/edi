This module is based on the `server_environment` module to use files for
configuration. So we can have a different configuration for each
environment (dev, test, integration, prod).  This module define the config
variables for the `account_invoice_export` module.

Exemple of the section to put in the configuration file::

    [transmit_method.transmition_method_code]
    destination_pwd: password,
    destination_user: user,
    destination_url: url,
