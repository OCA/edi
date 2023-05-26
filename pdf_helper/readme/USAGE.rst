Inside Odoo env::

    res = env["pdf.helper"].pdf_get_xml_files(pdf_filecontent)

Outside Odoo env::

    from odoo.addons.pdf_helper.utils import PDFParser
    [...]
    res = PDFParser(pdf_filecontent).get_xml_files()
