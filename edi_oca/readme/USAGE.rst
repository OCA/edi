After certain operations or manual execution, Exchange records will be generated.
This Exchange records might be input records or outputs records.

The change of state can be manually executed by the system or be managed through by
`ir.cron`.

Output Exchange records
~~~~~~~~~~~~~~~~~~~~~~~

An output record is intended to be used for exchange information from Odoo to another
system.

The flow of an output record should be:

* Creation
* Generation of data
* Validation of data
* Sending data
* Validation of data processed properly by the other party

Input Exchange records
~~~~~~~~~~~~~~~~~~~~~~

An input record is intended to be used for exchange information another system to odoo.

The flow of an input record should be:

* Creation
* Reception of data
* Checking data
* Processing data
