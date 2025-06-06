# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EdiversaSendInvoice(Component):
    _name = "ediversa.send.invoice"
    _usage = "output.send"
    _backend_type = "ediversa"
    _exchange_type = "ediversa_invoice_ouput"
    _inherit = ["edi.component.output.mixin"]

    def send(self):
        exchange_record = self.exchange_record
        if not exchange_record.company_id.use_edi_ediversa:
            error_msg = _(
                "Error when sending invoice exchange record "
                "%(identifier)s to Ediversa. Company %(company)s "
                "does not accept invoice Ediversa connection.",
                identifier=exchange_record.identifier,
                company=exchange_record.company_id.name,
            )
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        else:
            face = self.env.ref("edi_ediversa_oca.ediversa_backend")
            component = face._find_component(
                face._name,
                ["ediversa.api"],
                work_ctx={"exchange_record": self.env["edi.exchange.record"]},
            )
            external_ref = component.send_document(
                exchange_record.exchange_filename,
                exchange_record.exchange_file,
                exchange_record.company_id,
            )
            if not external_ref:
                error_msg = _(
                    "Error when sending invoice exchange record "
                    "%(identifier)s to Ediversa. The external reference "
                    "could not be retrieved.",
                    identifier=exchange_record.identifier,
                )
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            _logger.info(
                _(
                    "Invoice exchange record %(identifier)s has been sent to "
                    "Ediversa. The external reference is '%(external_ref)s'.",
                    identifier=exchange_record.identifier,
                    external_ref=external_ref,
                )
            )
