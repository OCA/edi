# Copyright 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        selection_add=[("ubl", "Universal Business Language (UBL)")], default="ubl"
    )
    embed_pdf_in_ubl_xml_invoice = fields.Boolean(
        string="Embed PDF in UBL XML Invoice",
        help="If active, the standalone UBL Invoice XML file will include the "
        "PDF of the invoice in base64 under the node "
        "'AdditionalDocumentReference'. For example, to be compliant with the "
        "e-fff standard used in Belgium, you should activate this option.",
    )
