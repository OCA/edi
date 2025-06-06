# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiversaApi(Component):
    _inherit = "ediversa.api"

    def get_sale_orders(self, company):
        docs = self.get_documents(company)
        env = "comedicloudws" if not company.edi_ediversa_test else "comedicloudwstest"
        namespaces = {
            "a": env,
        }
        doc_names = []
        for doc in docs:
            if doc.find("./a:type", namespaces).text == "ORDERS":
                doc_names.append(doc.find("./a:id", namespaces).text)
        return doc_names
