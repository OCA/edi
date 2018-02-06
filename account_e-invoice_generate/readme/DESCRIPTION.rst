This is a technical module needed to ensure compatibility between
the two electronic invoice generation modules: *account_invoice_ubl*
and *account_invoice_factur-x*. These 2 modules are able to embed an
XML file in the PDF invoice, but for the moment only one XML file can
be embedded in the PDF. And it can be useful to have both modules installed,
because, for example, you may need to generate Factur-X PDF invoices
for some customers and UBL XML files for other customers. So it adds
a configuration parameter to decide which XML format is embedded in the PDF.
