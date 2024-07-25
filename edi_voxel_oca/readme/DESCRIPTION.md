This is a base module that allows you to send and receive documents such
as Invoices, Sales Orders, Delivery Orders in XML format using the baVel
electronic platform belonging to Voxel Group.

Voxel Group is a company that offers leading solutions for B2B payments,
eInvoicing, VAT refund and supply chain via its baVel Platform. For more
information visit <https://www.voxelgroup.net/>.

This module doesn't do anything useful by itself, but it is used by
other modules:

- *edi_voxel_account_invoice* to send invoices to Voxel.
- *edi_voxel_stock_picking* to send delivery orders to Voxel.
- *edi_voxel_sale_order_import* to import a sale order received from
  Voxel.
