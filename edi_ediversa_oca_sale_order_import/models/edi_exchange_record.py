# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    def _cron_ediversa_import_sales(self):
        face = self.env.ref("edi_ediversa_oca.ediversa_backend")
        exchange_type = self.env["edi.exchange.type"].search(
            face._get_exchange_type_domain("ediversa_sale_input"), limit=1
        )
        for company in self.env["res.company"].search(
            [
                ("use_edi_ediversa", "=", True),
                ("edi_ediversa_user", "!=", False),
                ("edi_ediversa_password", "!=", False),
            ]
        ):
            component = face._find_component(
                face._name,
                ["ediversa.api"],
                safe=False,
                work_ctx={"exchange_record": self.env["edi.exchange.record"]},
            )
            documents = component.get_sale_orders(company)
            for document in documents:
                if not self.sudo().search(
                    [
                        ("backend_id", "=", face.id),
                        ("external_identifier", "=", document),
                        ("type_id", "=", exchange_type.id),
                    ],
                    limit=1,
                ):
                    face.create_record(
                        "ediversa_sale_input",
                        {
                            "edi_exchange_state": "input_pending",
                            "external_identifier": document,
                            "company_id": company.id,
                        },
                    )
