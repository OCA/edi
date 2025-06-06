# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class AccountMoveEdiEdiversaListener(Component):
    _name = "account.move.edi.ediversa.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def _get_exchange_record_vals(self, record):
        return {
            "model": record._name,
            "res_id": record.id,
            "company_id": record.company_id.id,
        }

    def on_post_account_move(self, records):
        for record in records:
            if record.edi_disable_auto or record.move_type not in [
                "out_invoice",
                "out_refund",
            ]:
                continue
            partner = record.partner_id
            if not partner.ediversa_send_invoice:
                continue
            backend = self.env.ref("edi_ediversa_oca.ediversa_backend")
            if not backend:
                continue
            exchange_type = self.env["edi.exchange.type"].search(
                backend._get_exchange_type_domain("ediversa_invoice_ouput"), limit=1
            )
            if record._has_exchange_record(exchange_type, backend):
                continue
            exchange_record = backend.create_record(
                exchange_type.code, self._get_exchange_record_vals(record)
            )
            exchange_record.with_delay().action_exchange_generate()
