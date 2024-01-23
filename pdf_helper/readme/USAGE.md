Inside Odoo env:

    res = env["pdf.helper"].pdf_get_xml_files(pdf_filecontent)

    new_pdf_filecontent = env["pdf.helper"].pdf_embed_xml(pdf_filecontent, filename, xml)

Outside Odoo env:

    from odoo.addons.pdf_helper.utils import PDFParser
    [...]
    res = PDFParser(pdf_filecontent).get_xml_files()
