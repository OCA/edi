This module extends the `sale_order_import_ubl` module to allow for importing
sales order automatically. To do so it adds a HTTP endpoint `ubl_api/sales`
accepting a POST requests containing the XML UBL formatted order.

On reception the endpoint will check the validity of the XML received and
if ok creates a queue.job that will import the sale.order and set it as confirmed.

By default the endpoint uses the api key authentication method. For security
reason the api key is not created by the module but the user that needs to be
linked to the key is.
