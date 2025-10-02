* Implement support for lines with all tax included, used for some localizations like Switzerland or scanned receipts.
* An graphical template builder.
* Once invoice2data 1.0 is published on PyPI: opt into its new APIs — the input-backend cascade (faster pdfium-first default + automatic fallback), runtime ``ai_fallback=True`` for LLM extraction when no template matches, ``raise_on_error=True`` for typed ``NoTemplateFoundError`` / ``RequiredFieldsMissingError`` instead of ``{}``, and ``pre_process_pdf`` returning the cleaned/smaller PDF so the wizard can re-attach it to the Odoo invoice in place of the raw upload.

Known Issues
* The input module is hard coded to use pdftotext parser and as a fallback to tesseract.
* Creation of the templates is still quite hard.
* The addres and company specific fields are parsed. Meaning it is possible to import an invoice which is issued to another company than yours!
