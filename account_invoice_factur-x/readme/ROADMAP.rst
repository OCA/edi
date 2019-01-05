* for Odoo v11, use the new hooks in the report code to embed the XML file inside the PDF file just after its generation and before it is saved as attachment.

* develop glue modules (or use hasattr() ?) to add to the XML file pieces of information that is carried out by fields defined in other modules such as sale or stock (customer order reference, incoterms, delivery address, etc...).
