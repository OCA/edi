To configure this module you have to belong to the access group
'Voxel manager' under 'Technical Settings', then:

#. Open a customer form view. In 'Sales & Purchases' page,
   check 'Enable Voxel' if you want to send delivery orders to this
   customer through Voxel.
#. Go to *Settings > Users & Companies > Companies*, open the companies you
   want to enable Voxel communication and set 'Enable Voxel' field to True.
#. In the login list, add the corresponding login for connecting with
   Voxel to send delivery orders. The final URL where delivery orders are going
   to be sent is '<Login URL>/Outbox'.
#. Save the form and edit it again, find 'Stock picking login' field and select
   the login to be used in delivery orders sending.
#. Select also the 'Send mode' to set when delivery orders will be sent:

  * On validate: Delivery orders will be sent to Voxel automatically when
    they are validated.
  * At fixed time: Delivery orders will be sent to Voxel automatically at
    a fixed time.
  * With delay: Delivery orders will be sent to Voxel automatically a certain
    time after they are validated.

Note:

This module enqueue the sending delivery orders to Voxel in jobs in the
background. To do that it uses queue_job module, so a configuration is required
according to that.
The jobs for sending invoices to Voxel are queued in the channel
``root.voxel_export channel``.
The sending status check jobs are queued in the channel
``root.voxel_status``.
