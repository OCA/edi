To configure this module you have to belong to the access group 'Voxel
manager' under 'Technical Settings', then:

1.  Open a customer form view. In 'Sales & Purchases' page, check
    'Enable Voxel' if you want to send invoices to this customer through
    Voxel.
2.  Go to *Settings \> Users & Companies \> Companies*, open the
    companies you want to enable Voxel communication and set 'Enable
    Voxel' field to True.
3.  In the login list, add the corresponding login for connecting with
    Voxel to send the invoices. The final URL where the invoices are
    going to be sent is '\<Login URL\>/Outbox'.
4.  Save the form and edit it again, find 'invoice login' field and
    select the login to be used in the invoice sending.
5.  Select also the 'Send mode' to set when the Invoice will be sent:

> - On validate: The invoice will be sent to Voxel automatically when
>   the invoice is validated.
> - At fixed time: The invoice will be sent to Voxel automatically at a
>   fixed time.
> - With delay: The invoice will be sent to Voxel automatically a
>   certain time after the invoice is validated.

Note:

This module enqueue the sending invoices to Voxel in jobs in the
background. To do that it uses queue_job module, so a configuration is
required according to that. The jobs for sending invoices to Voxel are
queued in the channel `root.voxel_export channel`. The sending status
check jobs are queued in the channel `root.voxel_status`.
