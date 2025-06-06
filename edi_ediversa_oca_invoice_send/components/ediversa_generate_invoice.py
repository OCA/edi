# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiversaGenerateInvoice(Component):
    _name = "ediversa.generate.invoice"
    _usage = "output.generate"
    _backend_type = "ediversa"
    _exchange_type = "ediversa_invoice_ouput"
    _inherit = ["edi.component.output.mixin"]

    def generate(self):
        invoice = self.env["account.move"].browse(self.exchange_record.res_id)
        data = ""
        if invoice.exists():
            header = invoice._ediversa_invoice_get_header()
            lines = invoice._ediversa_invoice_get_line()
            summary = invoice._ediversa_invoice_get_summary()
            for element in header + lines + summary:
                line = f"{'|'.join(list(element))}\n"
                data += line
        return data
