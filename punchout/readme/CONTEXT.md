[ This file is optional but strongly suggested to allow end-users to evaluate the
module's usefulness in their context. ]

This module set up the base of the connection to a punchout system. Sub module can be
created for example to create a purchase order from a shopping cart created in the
punchout platform. To do this, you can make your model inherit from "punchout.request"
and add the import process by inheriting "action_process" method.

Linked modules:

- punchout_environment : allows to configure a punchout backend through server
  environment files
- punchout_queue_job : link the punchout request to queue jobs, automatically call the
  process method when a response is received
