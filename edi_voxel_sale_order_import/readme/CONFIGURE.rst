To configure this module you have to belong to the access group
'Voxel manager' under 'Technical Settings', then:

#. Go to *Settings > Users & Companies > Companies*, open the companies you
   want to enable Voxel communication and set 'Enable Voxel' field to True.
#. In the login list, add the corresponding login for connecting with
   Voxel to import sales orders. The final URL from where sales order will be
   imported is '<Login URL>/Outbox'.
#. Save the form and edit it again, find 'Sale Order login' field and select
   the login to be used in the imports.
#. If you have the right access, go to
   *Settings > Technical > Automation > Scheduled Actions*, find the record
   named 'Edi Voxel: Get voxel sale order' and Adjust the data corresponding
   to that scheduled action, such as the frequency with which that action will
   be executed.

Note:

This module enqueue the imports in jobs in the background.
To do that it uses queue_job module, so a configuration is required
according to that.
The jobs for impots are queued in the channel ``root.voxel_import``.
