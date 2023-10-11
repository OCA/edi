* Implement support for lines with all tax included, used for some localizations like Switzerland or scanned receipts.
* An graphical template builder.

Known Issues
* The input module is hard coded to use pdftotext parser and as a fallback to tesseract.
* Creation of the templates is still quite hard.
* The addres and company specific fields are parsed. Meaning it is possible to import an invoice which is issued to another company than yours!
