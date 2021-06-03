This module adds support for the import of electronic RFQ or orders. This module provides the base methods to import electronic orders ; it requires additional modules to support specific order formats:

* module *sale_order_import_csv*: adds support for CSV orders,

* module *sale_order_import_ubl*: adds support for `Universal Business Language (UBL) <http://ubl.xml.org/>`_ RFQs and orders as:

  - XML file,
  - PDF file with an embedded XML file.
